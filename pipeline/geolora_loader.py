"""GEOLORA — Self-contained model definition for inference.

GEOLORA is a fine-tuned DFN-CLIP ViT-H/14-378 visual encoder with LoRA adapters
and a learned projection head. It produces L2-normalised 512-dim embeddings
suitable for bathroom object retrieval retrieval via cosine similarity (dot product).

This file is self-contained — no dependencies beyond torch and open_clip.
"""
from __future__ import annotations

import math

import open_clip
import torch
import torch.nn as nn
import torch.nn.functional as F


# ---------------------------------------------------------------------------
# LoRA primitives
# ---------------------------------------------------------------------------


class LoRALinear(nn.Module):
    """Drop-in replacement for nn.Linear with a low-rank adapter.

    output = W·x + (B·A·x) * (alpha / r)

    W is frozen. Only A and B are trained.
    B is initialised to zero so the adapter starts as an identity (no-op).
    """

    def __init__(self, linear: nn.Linear, r: int = 16, alpha: float = 32.0):
        super().__init__()
        self.linear = linear
        self.r = r
        self.scale = alpha / r

        in_f, out_f = linear.in_features, linear.out_features
        self.lora_A = nn.Linear(in_f, r, bias=False)
        self.lora_B = nn.Linear(r, out_f, bias=False)

        nn.init.kaiming_uniform_(self.lora_A.weight, a=math.sqrt(5))
        nn.init.zeros_(self.lora_B.weight)

        linear.weight.requires_grad_(False)
        if linear.bias is not None:
            linear.bias.requires_grad_(False)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.linear(x) + self.lora_B(self.lora_A(x)) * self.scale


def inject_lora(
    module: nn.Module,
    target_names: tuple[str, ...] = ("c_fc", "c_proj"),
    r: int = 16,
    alpha: float = 32.0,
) -> int:
    """Replace nn.Linear layers whose name matches a target with LoRALinear."""
    replaced = 0
    for name, child in list(module.named_children()):
        if isinstance(child, nn.Linear) and name in target_names:
            setattr(module, name, LoRALinear(child, r=r, alpha=alpha))
            replaced += 1
        else:
            replaced += inject_lora(child, target_names, r, alpha)
    return replaced


class LoRAMultiheadAttention(nn.Module):
    """Drop-in replacement for nn.MultiheadAttention with QKV LoRA adapters.

    open_clip fuses Q, K, V into a single in_proj_weight so we cannot wrap
    individual projections with LoRALinear. Instead we re-implement the
    attention forward using F.scaled_dot_product_attention, injecting LoRA
    corrections to Q, K, V activations before the dot product.

    Shared lora_A (down-projection) across Q/K/V; separate lora_B_q/k/v
    (up-projections). B matrices are initialised to zero (no-op at start).
    """

    def __init__(self, mha: nn.MultiheadAttention, r: int = 16, alpha: float = 32.0):
        super().__init__()
        D = mha.embed_dim
        self.embed_dim = D
        self.num_heads = mha.num_heads
        self.head_dim = D // mha.num_heads
        self.dropout = mha.dropout
        self.batch_first = mha.batch_first
        self.scale = alpha / r

        self.register_buffer("in_proj_weight", mha.in_proj_weight.data.clone())
        if mha.in_proj_bias is not None:
            self.register_buffer("in_proj_bias", mha.in_proj_bias.data.clone())
        else:
            self.register_buffer("in_proj_bias", None)
        self.register_buffer("out_proj_weight", mha.out_proj.weight.data.clone())
        if mha.out_proj.bias is not None:
            self.register_buffer("out_proj_bias", mha.out_proj.bias.data.clone())
        else:
            self.register_buffer("out_proj_bias", None)

        self.lora_A = nn.Linear(D, r, bias=False)
        self.lora_B_q = nn.Linear(r, D, bias=False)
        self.lora_B_k = nn.Linear(r, D, bias=False)
        self.lora_B_v = nn.Linear(r, D, bias=False)
        nn.init.kaiming_uniform_(self.lora_A.weight, a=math.sqrt(5))
        nn.init.zeros_(self.lora_B_q.weight)
        nn.init.zeros_(self.lora_B_k.weight)
        nn.init.zeros_(self.lora_B_v.weight)

    def forward(
        self,
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        need_weights: bool = True,
        attn_mask: torch.Tensor | None = None,
        key_padding_mask: torch.Tensor | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor | None]:
        if self.batch_first:
            query = query.transpose(0, 1)
            key = key.transpose(0, 1)
            value = value.transpose(0, 1)

        S, B, D = query.shape
        H, hd = self.num_heads, self.head_dim

        bias_q = self.in_proj_bias[:D] if self.in_proj_bias is not None else None
        bias_k = self.in_proj_bias[D : 2 * D] if self.in_proj_bias is not None else None
        bias_v = self.in_proj_bias[2 * D :] if self.in_proj_bias is not None else None

        q = F.linear(query, self.in_proj_weight[:D], bias_q)
        k = F.linear(key, self.in_proj_weight[D : 2 * D], bias_k)
        v = F.linear(value, self.in_proj_weight[2 * D :], bias_v)

        lora_q = self.lora_B_q(self.lora_A(query)) * self.scale
        lora_k = self.lora_B_k(self.lora_A(key)) * self.scale
        lora_v = self.lora_B_v(self.lora_A(value)) * self.scale
        q, k, v = q + lora_q, k + lora_k, v + lora_v

        q = q.reshape(S, B, H, hd).permute(1, 2, 0, 3)
        k = k.reshape(S, B, H, hd).permute(1, 2, 0, 3)
        v = v.reshape(S, B, H, hd).permute(1, 2, 0, 3)

        if attn_mask is not None and attn_mask.dim() == 2:
            attn_mask = attn_mask.unsqueeze(0).unsqueeze(0)

        dropout_p = self.dropout if self.training else 0.0
        out = F.scaled_dot_product_attention(
            q, k, v, attn_mask=attn_mask, dropout_p=dropout_p
        )

        out = out.permute(2, 0, 1, 3).reshape(S, B, D)
        out = F.linear(out, self.out_proj_weight, self.out_proj_bias)

        if self.batch_first:
            out = out.transpose(0, 1)
        return out, None


def inject_lora_attention(
    module: nn.Module, r: int = 16, alpha: float = 32.0
) -> int:
    """Replace all nn.MultiheadAttention layers with LoRAMultiheadAttention."""
    replaced = 0
    for name, child in list(module.named_children()):
        if isinstance(child, nn.MultiheadAttention):
            setattr(module, name, LoRAMultiheadAttention(child, r=r, alpha=alpha))
            replaced += 1
        else:
            replaced += inject_lora_attention(child, r, alpha)
    return replaced


# ---------------------------------------------------------------------------
# Main model
# ---------------------------------------------------------------------------


class Geolora(nn.Module):
    """DFN-CLIP visual encoder with LoRA adapters and a projection head.

    Produces L2-normalised embeddings of dimensionality ``embed_dim`` (default 512).

    The base model (DFN-CLIP ViT-H/14-378, ~1B params) is downloaded from
    open_clip on first use and frozen. Only the LoRA adapters (~31 MB) and
    projection head are loaded from the checkpoint.

    Args:
        lora_r: LoRA rank.
        lora_alpha: LoRA alpha scaling factor.
        embed_dim: Output embedding dimensionality.
        device: Torch device string.
        lora_targets: Names of MLP linear layers to inject LoRA into.
        legacy_proj: Use single-layer projection head (older checkpoints).
        lora_qkv: Inject LoRA into Q/K/V attention projections.
    """

    MODEL_NAME = "ViT-H-14-378-quickgelu"
    PRETRAINED = "dfn5b"

    def __init__(
        self,
        lora_r: int = 16,
        lora_alpha: float = 32.0,
        embed_dim: int = 512,
        device: str = "cpu",
        lora_targets: tuple[str, ...] = ("c_fc", "c_proj"),
        legacy_proj: bool = False,
        lora_qkv: bool = False,
    ):
        super().__init__()

        clip_model, _, _ = open_clip.create_model_and_transforms(
            self.MODEL_NAME, pretrained=self.PRETRAINED, device=device,
        )
        self.visual = clip_model.visual

        for p in self.visual.parameters():
            p.requires_grad_(False)

        inject_lora(self.visual, target_names=lora_targets, r=lora_r, alpha=lora_alpha)

        if lora_qkv:
            inject_lora_attention(self.visual, r=lora_r, alpha=lora_alpha)

        try:
            backbone_dim = clip_model.visual.output_dim
        except AttributeError:
            backbone_dim = 1024

        if legacy_proj:
            self.proj = nn.Sequential(
                nn.Linear(backbone_dim, embed_dim, bias=False),
                nn.LayerNorm(embed_dim),
            )
        else:
            self.proj = nn.Sequential(
                nn.Linear(backbone_dim, backbone_dim, bias=False),
                nn.GELU(),
                nn.LayerNorm(backbone_dim),
                nn.Linear(backbone_dim, embed_dim, bias=False),
                nn.LayerNorm(embed_dim),
            )

    def encode_image(self, x: torch.Tensor) -> torch.Tensor:
        """Encode a batch of images into L2-normalised embeddings.

        Args:
            x: Preprocessed image tensor of shape (B, 3, 378, 378).

        Returns:
            L2-normalised embeddings of shape (B, embed_dim).
        """
        features = self.visual(x)
        emb = self.proj(features)
        return F.normalize(emb, dim=-1)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.encode_image(x)


# ---------------------------------------------------------------------------
# Convenience loader
# ---------------------------------------------------------------------------


def load_geolora(
    checkpoint_path: str,
    device: str = "cpu",
) -> tuple[Geolora, torch.nn.Module]:
    """Load a Geolora model from a checkpoint.

    Args:
        checkpoint_path: Path to a .pt checkpoint file.
        device: Device to load the model onto.

    Returns:
        Tuple of (model, preprocess) where preprocess is a torchvision
        transform that prepares PIL images for the model.
    """
    import torchvision.transforms as T

    ckpt = torch.load(checkpoint_path, map_location=device, weights_only=False)
    cfg = ckpt["config"]
    state = ckpt["model_state"]

    # Auto-detect architecture from checkpoint
    legacy_proj = state["proj.0.weight"].shape[0] == cfg["embed_dim"]
    lora_qkv = any("lora_B_q" in k for k in state)

    model = Geolora(
        lora_r=cfg["lora_r"],
        lora_alpha=cfg["lora_alpha"],
        embed_dim=cfg["embed_dim"],
        device=device,
        lora_targets=("c_fc", "c_proj"),
        legacy_proj=legacy_proj,
        lora_qkv=lora_qkv,
    )
    model = model.to(device)
    _, unexpected = model.load_state_dict(state, strict=False)
    if unexpected:
        raise RuntimeError(f"Unexpected keys in checkpoint: {unexpected}")
    model.eval()

    image_size = cfg.get("image_size", 378)
    preprocess = T.Compose([
        T.Resize(image_size, interpolation=T.InterpolationMode.BICUBIC),
        T.CenterCrop(image_size),
        T.ToTensor(),
        T.Normalize(
            mean=(0.48145466, 0.4578275, 0.40821073),
            std=(0.26862954, 0.26130258, 0.27577711),
        ),
    ])

    return model, preprocess
