# MODULE FOR GENERATING EMBEDDINGS

import numpy as np
import torch
from PIL import Image
from transformers import AutoProcessor, AutoModel
import open_clip
import torchvision.transforms as T
from pathlib import Path
import sys

'''
BASE CLIP EMBEDDINGS (best for now)
'''

_base_clip_model = None
_base_clip_preprocess = None

def get_base_clip_model():
    global _base_clip_model, _base_clip_preprocess
    if _base_clip_model is None:
        # explicitly pulls directly from Apple's HuggingFace repository URL
        model, _, _ = open_clip.create_model_and_transforms(
            'hf-hub:apple/DFN5B-CLIP-ViT-H-14-378'
        )
        device = "cuda" if torch.cuda.is_available() else "cpu"
        _base_clip_model = model.visual.to(device).eval()
        
        _base_clip_preprocess = T.Compose([
            T.Resize(378, interpolation=T.InterpolationMode.BICUBIC),
            T.CenterCrop(378),
            T.ToTensor(),
            T.Normalize(
                mean=(0.48145466, 0.4578275, 0.40821073),
                std=(0.26862954, 0.26130258, 0.27577711),
            ),
        ])
    return _base_clip_model, _base_clip_preprocess

def generate_base_clip_embedding(image: Image.Image) -> np.ndarray:
    model, preprocess = get_base_clip_model()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    tensor = preprocess(image).unsqueeze(0).to(device)
    with torch.no_grad():
        embedding = model(tensor).squeeze().cpu().numpy()
        
    # L2 normalize so cosine similarity works correctly
    norm = np.linalg.norm(embedding)
    if norm > 1e-8:
        embedding = embedding / norm
    return embedding

'''
GEOLORA 4 EMBEDDINGS
'''
GEOLORA4_CHECKPOINT = Path(__file__).resolve().parent.parent / "models" / "geolora_checkpoints" / "epoch_4.pt"

_geolora_model = None
_geolora_preprocess = None

def get_geolora4_model():
    global _geolora_model, _geolora_preprocess
    if _geolora_model is None:
        from .geolora_loader import load_geolora
        device = "cuda" if torch.cuda.is_available() else "cpu"
        _geolora_model, _geolora_preprocess = load_geolora(str(GEOLORA4_CHECKPOINT), device=device)
        _geolora_model.eval()
    return _geolora_model, _geolora_preprocess

def generate_geolora4_embedding(image: Image.Image) -> np.ndarray:
    model, preprocess = get_geolora4_model()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    tensor = preprocess(image).unsqueeze(0).to(device)
    with torch.no_grad():
        embedding = model(tensor)
    return embedding.squeeze().cpu().numpy()

'''
GEOLORA 3 EMBEDDINGS
'''
geolora3_CHECKPOINT = Path(__file__).resolve().parent.parent / "models" / "geolora_checkpoints" / "epoch_3.pt"

_geolora_model = None
_geolora_preprocess = None

def get_geolora3_model():
    global _geolora_model, _geolora_preprocess
    if _geolora_model is None:
        from .geolora_loader import load_geolora
        device = "cuda" if torch.cuda.is_available() else "cpu"
        _geolora_model, _geolora_preprocess = load_geolora(str(geolora3_CHECKPOINT), device=device)
        _geolora_model.eval()
    return _geolora_model, _geolora_preprocess

def generate_geolora3_embedding(image: Image.Image) -> np.ndarray:
    model, preprocess = get_geolora3_model()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    tensor = preprocess(image).unsqueeze(0).to(device)
    with torch.no_grad():
        embedding = model(tensor)
    return embedding.squeeze().cpu().numpy()

'''
GEOLORA 2 EMBEDDINGS
'''
geolora2_CHECKPOINT = Path(__file__).resolve().parent.parent / "models" / "geolora_checkpoints" / "epoch_2.pt"

_geolora_model = None
_geolora_preprocess = None

def get_geolora2_model():
    global _geolora_model, _geolora_preprocess
    if _geolora_model is None:
        from .geolora_loader import load_geolora
        device = "cuda" if torch.cuda.is_available() else "cpu"
        _geolora_model, _geolora_preprocess = load_geolora(str(geolora2_CHECKPOINT), device=device)
        _geolora_model.eval()
    return _geolora_model, _geolora_preprocess

def generate_geolora2_embedding(image: Image.Image) -> np.ndarray:
    model, preprocess = get_geolora2_model()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    tensor = preprocess(image).unsqueeze(0).to(device)
    with torch.no_grad():
        embedding = model(tensor)
    return embedding.squeeze().cpu().numpy()

'''
GEOLORA 1 EMBEDDINGS
'''
geolora1_CHECKPOINT = Path(__file__).resolve().parent.parent / "models" / "geolora_checkpoints" / "epoch_1.pt"

_geolora_model = None
_geolora_preprocess = None

def get_geolora1_model():
    global _geolora_model, _geolora_preprocess
    if _geolora_model is None:
        from .geolora_loader import load_geolora
        device = "cuda" if torch.cuda.is_available() else "cpu"
        _geolora_model, _geolora_preprocess = load_geolora(str(geolora1_CHECKPOINT), device=device)
        _geolora_model.eval()
    return _geolora_model, _geolora_preprocess

def generate_geolora1_embedding(image: Image.Image) -> np.ndarray:
    model, preprocess = get_geolora1_model()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    tensor = preprocess(image).unsqueeze(0).to(device)
    with torch.no_grad():
        embedding = model(tensor)
    return embedding.squeeze().cpu().numpy()

'''
FLORA EMBEDDINGS
'''
FLORA_CHECKPOINT = Path(__file__).resolve().parent.parent / "models" / "weights-41.pt"

_flora_model = None
_flora_preprocess = None

def get_flora_model():
    global _flora_model, _flora_preprocess
    if _flora_model is None:
        from .flora_loader import load_flora
        device = "cuda" if torch.cuda.is_available() else "cpu"
        _flora_model, _flora_preprocess = load_flora(str(FLORA_CHECKPOINT), device=device)
        _flora_model.eval()
    return _flora_model, _flora_preprocess

def generate_flora_embedding(image: Image.Image) -> np.ndarray:
    model, preprocess = get_flora_model()
    device = "cuda" if torch.cuda.is_available() else "cpu"
    tensor = preprocess(image).unsqueeze(0).to(device)
    with torch.no_grad():
        embedding = model(tensor)
    return embedding.squeeze().cpu().numpy()

'''
DINO EMBEDDINGS
'''

DINOV2_MODEL_ID = "facebook/dinov2-base"
_device = None
_model = None
_processor = None

def get_dinov2_model(device: str, model_id: str = DINOV2_MODEL_ID):
    model = AutoModel.from_pretrained(model_id).to(device)
    processor = AutoProcessor.from_pretrained(model_id)
    return model, processor

def generate_dino_embedding(image: Image.Image) -> np.ndarray:
    global _device
    global _model
    global _processor

    # wait for download on first run
    if _device is None:
        _device = "cuda" if torch.cuda.is_available() else "cpu"
    if _model is None or _processor is None:
        _model, _processor = get_dinov2_model(_device)

    inputs = _processor(images=image, return_tensors="pt").to(_device)
    with torch.no_grad():
        outputs = _model(**inputs)
    # embedding = outputs.last_hidden_state.mean(dim=1) ?? maybe better
    # shape -> (768,) required for our DB
    return outputs.last_hidden_state[:, 0].squeeze().cpu().numpy()

