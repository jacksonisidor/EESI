# EESI — Everything Everywhere Search Index

EESI is a computer-vision system that helps investigators compare visually distinctive bathroom fixtures and fittings against a large, geotagged reference index. Investigators upload evidence images on a **local device**; the system extracts **embeddings** (mathematical fingerprints that cannot be reconstructed into the original image) and queries a remote reference database for visually similar objects with known geographic metadata.

This repository contains:

- The **query pipeline** (`pipeline/`) — detection, embedding, and similarity search
- The **investigator desktop app** (`app/`) — Electron + React UI
- **Model weights** (`models/`) — YOLO detector and optional LoRA checkpoints
- Configuration templates (`.env.example`) for database and AWS access

---

## Table of contents

1. [Project overview](#1-project-overview)
2. [System architecture](#2-system-architecture)
3. [Repository structure](#3-repository-structure)
4. [Setup](#4-setup)
   - [Local machine vs EC2](#42-local-development-machine-vs-ec2-instance)
5. [Running the investigator app](#5-running-the-investigator-app) ← **start here for the UI**
6. [Programmatic usage](#6-programmatic-usage)
7. [Database schema](#7-database-schema)
8. [Models](#8-models)
9. [Configuration](#9-configuration)
10. [Troubleshooting](#11-troubleshooting)

---

## 1. Project overview

Law-enforcement investigations often include large volumes of visual evidence. In bathroom scenes, regionally distinctive fixtures (toilets, sinks, outlets, shower enclosures, etc.) can narrow geographic hypotheses when compared against a global reference set.

EESI builds on ideas from GEN’s **Uniform Intelligence Hub (UIH)**, which matches school-uniform logos. EESI generalizes that approach to **everyday bathroom objects** indexed from publicly available, geotagged listing photos (not CSAM).

**Privacy architecture:** Raw CSAM must not leave the investigator machine. The Electron app runs detection and embedding **locally**; only embeddings and query parameters are sent to the database layer for similarity search. Match **thumbnail images** are fetched from S3 by the pipeline when displaying results (reference photos only).

**Reference scale (as of project handoff):** 273,000+ cropped objects across 236+ countries, stored in PostgreSQL with pgvector and AWS S3.

---

## 2. System architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  Investigator device (Electron app + Python pipeline)            │
│  • Upload full image OR pre-cropped object                       │
│  • CLIP bathroom filter → YOLO detect → crop → embed (local)   │
│  • Only embeddings + labels leave for DB query (privacy model)   │
└────────────────────────────┬────────────────────────────────────┘
                             │ cosine similarity query
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  EESI server infrastructure (GEN EC2 + AWS)                      │
│  • PostgreSQL + pgvector (embeddings + metadata)                 │
│  • S3 bucket (reference crop images)                             │
└─────────────────────────────────────────────────────────────────┘
```

### Query path 1 — Full bathroom image

1. **CLIP filter** (`clip_filter.py`) — zero-shot check that the scene is a bathroom  
2. **YOLO detector** (`yolo_detector.py`) — 13 object classes, bounding boxes  
3. **Cropper** (`cropper.py`) — isolate each detection  
4. **Embedder** (`embedder.py`) — **base DFN-CLIP ViT-H/14-378** (production default)  
5. **Query** (`query.py`) — top-K cosine matches per detected label from PostgreSQL  
6. **S3** (`s3.py`) — fetch match images for display  

### Query path 2 — Pre-cropped object with known label

Skips steps 1–3. Embeds the crop and queries the database for that label only (`query_from_crop`).

### Ingestion path (reference DB population)

`ingest.py` runs the same core steps as path 1, then uploads crops to S3 and inserts rows into PostgreSQL. Used when building the reference index (scraping workflow), not during investigator queries.

### Output fields (per match)

| Field | Description |
|--------|-------------|
| `label` | Object class (e.g. `toilet`, `sink`) |
| `city`, `state`, `country`, `continent` | Geographic metadata |
| `lat`, `long` | Coordinates |
| `image_path` | `s3://…` URI in the reference bucket |
| `distance` | pgvector cosine distance (lower = more similar) |

---

## 3. Repository structure

```
EESI/
├── README.md                 # This file
├── .env.example              # Copy to .env — DB and AWS settings
├── requirements.txt          # Dependencies for query pipeline and app
├── examples/
│   └── query_example.py      # CLI example for both query paths
├── pipeline/                 # Python ML + database package
│   ├── core.py               # Shared: filter → detect → crop → embed
│   ├── clip_filter.py        # Bathroom vs non-bathroom (CLIP zero-shot)
│   ├── yolo_detector.py      # Custom YOLO26s detector
│   ├── cropper.py            # Bounding-box crops
│   ├── embedder.py           # DFN-CLIP, Flora, GeoLoRA, DINOv2 options
│   ├── flora_loader.py       # Flora LoRA checkpoint loader
│   ├── geolora_loader.py     # GeoLoRA checkpoint loader
│   ├── query.py              # Investigator query + deduplication
│   ├── db.py                 # PostgreSQL connection + insert
│   ├── s3.py                 # S3 upload/download
│   └── ingest.py             # Reference ingestion (S3 + DB)
├── models/                   # Trained weights (required for full pipeline)
│   ├── object_detector_best.pt   # Fine-tuned YOLO (13 classes)
│   ├── weights-41.pt             # Flora LoRA checkpoint (optional)
│   ├── yolo26s.pt                # Base YOLO weights (training artifact)
│   └── geolora_checkpoints/    # GeoLoRA epochs 1–4 (optional)
└── app/                      # GEN Investigator Electron desktop app
    ├── electron-main.ts      # Main process; spawns Python pipeline
    ├── electron-preload.ts   # Secure IPC bridge
    ├── src/App.tsx           # React UI
    ├── package.json
    ├── start-dev.sh          # One-command dev launcher
    ├── README.md             # App-specific developer notes
    └── QUICKSTART.md         # Short app quick reference
```

**Not in this repo:** scraping scripts, EC2 provisioning, and the populated production database (hosted on GEN infrastructure).

---

## 4. Setup

### 4.1 Prerequisites

| Component | Version / notes |
|-----------|-----------------|
| **Python** | 3.11+ recommended |
| **Node.js** | 18+ (for Electron app) |
| **PostgreSQL** | With **pgvector** extension; reference DB on GEN EC2 |
| **AWS** | Credentials with read access to the EESI S3 bucket |
| **GPU** | Optional; CUDA or Apple MPS speeds up embedding and YOLO |

### 4.2 Local development machine vs EC2 instance

The reference **PostgreSQL database runs on GEN’s EC2 instance** (g4dn.xlarge). **S3** holds reference images. How you connect depends on **where you run the code**:

| | **Local machine** (Mac/laptop) | **On the EC2 instance** (SSH session) |
|---|-------------------------------|--------------------------------------|
| **Typical use** | Investigator **Electron app**, local embedding + remote DB query | DB admin, Python scripts, GPU-heavy batch jobs, `psql` |
| **PostgreSQL** | **SSH tunnel required** — DB is not public on the internet | Connect to `localhost:5432` directly (no tunnel) |
| **S3** | `aws sso login --profile <aws-profile>` on your laptop | Same SSO login on EC2 (if configured) or instance IAM role |
| **Electron UI** | ✅ Supported (recommended) | ❌ Not practical (no desktop display); use local machine instead |

> **Important:** If you are on your **own laptop** (not logged into the EC2 VM), you **must** open an SSH tunnel before the app or `query_example.py` can reach the database. Without it, you will see connection refused errors on port 5432.

#### AWS access (SSO)

Obtain your **AWS SSO start URL**, **CLI profile name**, and **EC2 connection details** (host, SSH user, DB credentials) from your GEN administrator or internal runbook. Do not commit these values to the repository.

#### SSH into the EC2 instance

When you need a shell on the database/GPU host:

```bash
ssh <username>@<ec2-host>
```

#### SSH tunnel — local machine → database on EC2

**When required:** Any time you run the Electron app, `query_example.py`, or other pipeline code on your **local machine** while the database lives on EC2.

Run this on your **local** terminal (leave it open while using the app or local Python scripts):

```bash
ssh -L 5432:localhost:5432 <username>@<ec2-host> -N
```

- `-L 5432:localhost:5432` forwards your laptop’s port 5432 to PostgreSQL on the EC2 instance.
- `-N` means “no remote shell” (tunnel only).

**Run in the background** (so you can use the same terminal for other work):

```bash
ssh -f -L 5432:localhost:5432 <username>@<ec2-host> -N
```

Then in `.env` at the repo root:

```bash
EESI_DB_HOST=localhost
EESI_DB_PORT=5432
```

If local port 5432 is already in use (e.g. local Postgres), pick another local port:

```bash
ssh -f -L 15432:localhost:5432 <username>@<ec2-host> -N
# .env: EESI_DB_PORT=15432
```

**Checklist before `npm run electron-dev` on a local machine:**

1. SSH tunnel running (or background `-f` tunnel)
2. `.env` filled in with DB credentials (from GEN)
3. AWS SSO session active for S3 (see below)
4. Python venv active with `requirements.txt` installed

#### AWS SSO — S3 access (local or EC2)

Reference images are stored in S3. After your team configures the AWS CLI with SSO:

```bash
aws sso login --profile <aws-profile>
```

Verify access (bucket name from GEN):

```bash
aws s3 ls s3://<bucket-name> --profile <aws-profile>
```

For `boto3` in the pipeline to use this profile, export before launching the app:

```bash
export AWS_PROFILE=<aws-profile>
```

#### On EC2 — direct database access

After SSH into the instance (normal shell, not the tunnel-only `-N` session):

```bash
sudo -u postgres psql -d eesi
```

Use this for SQL inspection, row counts, and debugging — not required for the Electron app if you tunnel from your laptop.

#### Shutting down the EC2 instance

**Only when GEN approves** (stops GPU/DB host for everyone):

```bash
sudo shutdown -h now
```

Run **after** SSH login on the instance. Do not run from your local machine.

#### Summary workflow

**Local investigator / developer (most common):**

```bash
# Terminal 1 — tunnel (keep open; local machine only)
ssh -L 5432:localhost:5432 <username>@<ec2-host> -N

# Terminal 2 — app
aws sso login --profile <aws-profile>
export AWS_PROFILE=<aws-profile>
cd /path/to/EESI
source .venv/bin/activate
cd app && npm run electron-dev
```

**On EC2 (scripts / DB only):**

```bash
ssh <username>@<ec2-host>
cd /path/to/EESI   # clone repo on instance if needed
source .venv/bin/activate
python examples/query_example.py --image sample.jpg
# DB: EESI_DB_HOST=localhost in .env — no tunnel
```

### 4.3 Clone and model weights

Ensure these files exist under `models/`:

- `object_detector_best.pt` — **required** for full-image path  
- `weights-41.pt` — only if using Flora embeddings  
- `geolora_checkpoints/epoch_*.pt` — only if using GeoLoRA embeddings  

First run will also download Hugging Face / OpenCLIP base weights (~several GB).

### 4.4 Python environment

From the repository root:

```bash
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 4.5 Environment file

```bash
cp .env.example .env
```

Edit `.env` with database credentials and optional overrides (see [Configuration](#9-configuration)).

- **Local machine:** `EESI_DB_HOST=localhost` with the [SSH tunnel](#ssh-tunnel--local-machine--database-on-ec2) running.
- **On EC2:** `EESI_DB_HOST=localhost` with no tunnel.

### 4.6 AWS credentials

GEN typically uses **AWS SSO**. Configure your CLI profile per internal documentation, then see [AWS SSO — S3 access](#aws-sso--s3-access-local-or-ec2).

Default bucket: `eesi-students-368003222772` (override with `EESI_S3_BUCKET` in `.env`).

### 4.7 Node dependencies (app)

```bash
cd app
npm install
```

---

## 5. Running the investigator app

This is the primary way GEN investigators interact with EESI.

### Quick start (recommended)

From the repository root:

```bash
# 1. Activate Python venv (same shell or ensure PYTHON_EXECUTABLE points to it)
source .venv/bin/activate

# 2. Local machine only: SSH tunnel to EC2 DB (see §4.2)
#    ssh -L 5432:localhost:5432 <username>@<ec2-host> -N
# 3. aws sso login --profile <aws-profile> && export AWS_PROFILE=<aws-profile>
# 4. Ensure .env exists at repo root

# 5. Launch the app (you must already be in app/ — do not run "cd app" twice)
cd app
npm run electron-dev
```

**Or** use the helper script:

```bash
./app/start-dev.sh
```

What happens:

1. Electron main process is compiled to `app/dist/`
2. Vite serves the React UI at **http://localhost:5173** (dev only)
3. Electron window opens — **use the Electron window**, not the browser tab
4. Upload an image → choose **Full Image** or **Crop + Label** → **Analyze Image**

### Production-style run

```bash
cd app
npm run build:electron
npm run build:vite
NODE_ENV=production npm run electron
```

Package installers: `npm run build` (uses `electron-builder`).

### App usage modes

| Mode | When to use |
|------|-------------|
| **Full Image** | Upload a full bathroom photo; YOLO finds objects automatically |
| **Crop + Label** | Upload a pre-cropped object; select the object class (toilet, sink, etc.) |

Results show geographic location text, similarity score, and reference thumbnails (loaded from S3). Use **Export Results** to save JSON locally.

### Environment variables for the app

| Variable | Purpose |
|----------|---------|
| `PYTHON_EXECUTABLE` | Path to Python with pipeline installed (default: `python3`) |
| `EESI_ROOT` | Repository root (auto-detected from `app/dist/`) |
| `VITE_DEV_SERVER_PORT` | Dev UI port (default `5173`) |
| `VITE_DEV_SERVER_URL` | Full dev URL if port/host customized |

All `EESI_*` database and S3 variables in `.env` are loaded by the Python subprocess.

### Port 5173 already in use

```bash
# macOS / Linux
lsof -ti :5173 | xargs kill -9

# Or use another port:
export VITE_DEV_SERVER_PORT=5174
export VITE_DEV_SERVER_URL=http://localhost:5174
cd app && npm run electron-dev
```

---

## 6. Programmatic usage

Run from the repository root with `.env` configured and venv active.

### Path 1 — Full image

```python
from PIL import Image
from pipeline.query import query_from_image

image = Image.open("path/to/bathroom.jpg")
results = query_from_image(image, k=5)

# results: dict[label -> list of match dicts], or None if filtered out
if results:
    for label, matches in results.items():
        print(label, matches[0]["country"], matches[0]["distance"])
```

### Path 2 — Pre-cropped object

```python
from PIL import Image
from pipeline.query import query_from_crop

crop = Image.open("path/to/toilet_crop.jpg")
matches = query_from_crop(crop, label="toilet", k=5)

for m in matches:
    print(m["city"], m["country"], m["distance"], m["image_path"])
```

### CLI example

```bash
python examples/query_example.py --image path/to/bathroom.jpg
python examples/query_example.py --crop path/to/sink.jpg --label sink -k 10
```

### Shared pipeline only (no database)

```python
from PIL import Image
from pipeline.core import process_image, process_crop

full = process_image(Image.open("bathroom.jpg"))   # list of dicts with crop + embedding
crop = process_crop(Image.open("toilet.jpg"), "toilet")
```

---

## 7. Database schema

Table: **`objects`**

| Column | Type | Description |
|--------|------|-------------|
| `id` | serial | Primary key |
| `label` | text | Object class (13 YOLO classes) |
| `city`, `state`, `country`, `continent` | text | Geographic hierarchy |
| `lat`, `long` | float | Coordinates |
| `image_path` | text | `s3://bucket/objects/<listing_id>/<label>_<index>.jpg` |
| `caption` | text | Optional caption (unused in current query path) |
| `dino_embedding` | vector(768) | DINOv2 baseline |
| `flora_embedding` | vector(512) | Flora LoRA (UIH-shared architecture) |
| `base_clip_embedding` | vector(1024) | **Production query column** (DFN-CLIP visual) |
| `geolora_embedding_e1` … `e4` | vector(512) | GeoLoRA training checkpoints |
| `created_at` | timestamp | Insert time |

Similarity uses pgvector **cosine distance** (`<=>`). Queries filter by `label` so toilets are only compared to toilets.

---

## 8. Models

| Model | Role | Weights / source |
|-------|------|------------------|
| **roomLuxuryAnnotater** | Bathroom CLIP filter | `strollingorange/roomLuxuryAnnotater` (Hugging Face) |
| **YOLO26s (custom)** | 13-class object detection | `models/object_detector_best.pt` |
| **DFN-CLIP ViT-H/14-378** | **Production embeddings** | `hf-hub:apple/DFN5B-CLIP-ViT-H-14-378` via `open_clip` |
| **Flora** | 512-d LoRA on DFN-CLIP (UIH lineage) | `models/weights-41.pt` |
| **GeoLoRA** | Geographic fine-tune (4 epochs) | `models/geolora_checkpoints/epoch_*.pt` |
| **DINOv2-base** | 768-d baseline embedder | `facebook/dinov2-base` |

**YOLO classes:** `toilet`, `sink`, `mirror`, `shower`, `showerhead`, `bathtub`, `floor`, `rug`, `brand`, `outlet`, `plant`, `bidet`, `window`.

**Evaluation recommendation:** Use **base DFN-CLIP** for production (`EESI_EMBEDDING_COLUMN=base_clip_embedding`). It achieved the strongest geographic retrieval metrics in holdout evaluation (median closest match ~367 km at K=10). GeoLoRA showed promise but needs more training compute to match base CLIP.

Switch embedding column (must match stored DB vectors):

```bash
# .env
EESI_EMBEDDING_COLUMN=flora_embedding
```

Then use `generate_flora_embedding` in `core.py` instead of `generate_base_clip_embedding` if re-indexing or experimenting locally.

---

## 9. Configuration

Copy `.env.example` → `.env` at the **repository root**.

| Variable | Default | Description |
|----------|---------|-------------|
| `EESI_DB_HOST` | `localhost` | PostgreSQL host |
| `EESI_DB_PORT` | `5432` | PostgreSQL port |
| `EESI_DB_NAME` | `eesi` | Database name |
| `EESI_DB_USER` | `eesi` | Database user |
| `EESI_DB_PASSWORD` | *(empty)* | Database password |
| `EESI_S3_BUCKET` | `eesi-students-368003222772` | Reference image bucket |
| `EESI_EMBEDDING_COLUMN` | `base_clip_embedding` | pgvector column for search |
| `PYTHON_EXECUTABLE` | `python3` | Python for Electron subprocess |
| `EESI_ROOT` | auto | Repo root override |
| `VITE_DEV_SERVER_PORT` | `5173` | Vite dev port |
| `VITE_DEV_SERVER_URL` | `http://localhost:5173` | URL Electron loads in dev |

| `AWS_PROFILE` | — | Your SSO profile name (export in shell before running the app) |

Standard AWS variables (`AWS_ACCESS_KEY_ID`, etc.) apply if not using SSO profiles.


## 11. Troubleshooting

| Symptom | Likely cause | Fix |
|---------|----------------|-----|
| `Electron bridge unavailable` | Opened Vite URL in browser | Use the **Electron** window (`npm run electron-dev`) |
| `Python script failed` / import errors | Wrong Python or missing deps | Set `PYTHON_EXECUTABLE` to venv python; `pip install -r requirements.txt` |
| DB connection refused | No SSH tunnel (local) or wrong `.env` | Start tunnel: `ssh -L 5432:localhost:5432 <username>@<ec2-host> -N`; see [§4.2](#42-local-development-machine-vs-ec2-instance) |
| S3 / `image_retrieval_error` in matches | SSO session expired | Re-run `aws sso login --profile <aws-profile>` and verify with `aws s3 ls` |
| `cd: no such file or directory: app` | Already inside `app/` | Run `npm run electron-dev` only (no extra `cd app`) |
| `No objects detected` | Non-bathroom or low-confidence YOLO | Try **Crop + Label** mode |
| Slow first query | Model download / GPU init | Expected; subsequent queries faster |
| pgvector dimension error | Wrong `EESI_EMBEDDING_COLUMN` | Must match column used when indexing |
| Port 5173 in use | Another Vite process | Kill process or change `VITE_DEV_SERVER_PORT` |

For app-specific details, see [`app/README.md`](app/README.md) and [`app/QUICKSTART.md`](app/QUICKSTART.md).

---
