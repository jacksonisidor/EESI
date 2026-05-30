# EESI — Everything Everywhere Search Index

EESI helps investigators compare visually distinctive bathroom fixtures against a large, geotagged reference index. Investigators run the **desktop app on their local machine**. The app detects objects, generates embeddings locally, and queries a remote reference database for similar objects with geographic metadata.

**Privacy:** Evidence images stay on the investigator device. Only embeddings are sent to the database for similarity search. Match thumbnails are reference photos fetched from S3.

**Reference scale:** 273,000+ cropped objects across 236+ countries (PostgreSQL + pgvector on GEN EC2, images on S3).

---

## Table of contents

1. [Project overview](#project-overview)
2. [System architecture](#system-architecture)
3. [Repository structure](#repository-structure)
4. [Setup (one-time)](#setup-one-time)
5. [Run the app](#run-the-app)
6. [Using the app](#using-the-app)
7. [Database schema](#database-schema)
8. [Models](#models)
9. [Troubleshooting](#troubleshooting)

---

## Project overview

EESI builds on GEN’s **Uniform Intelligence Hub (UIH)** (school-uniform logo matching). It extends that idea to **everyday bathroom objects** — toilets, sinks, outlets, shower enclosures, etc. — indexed from publicly available geotagged photos.

Investigators upload a bathroom image or a pre-cropped object. The system returns visually similar reference objects with city, country, coordinates, and similarity scores to help narrow geographic hypotheses.

---

## System architecture

**What runs where:**

| Where | What |
|-------|------|
| **Your laptop (this repo)** | Electron app + Python pipeline — detection, embedding, UI |
| **GEN EC2** | PostgreSQL database (embeddings + metadata) |
| **AWS S3** | Reference crop images |

```
Your laptop                         GEN infrastructure
┌─────────────────────────┐         ┌─────────────────────────┐
│  Electron app (app/)    │         │  PostgreSQL + pgvector  │
│  Python pipeline        │ ─query─▶│  (on EC2)               │
│  (local ML inference)   │         │                         │
│                         │ ◀─S3─── │  Reference images (S3)  │
└─────────────────────────┘         └─────────────────────────┘
         ▲
         │ SSH tunnel (local only) forwards localhost:5432 → EC2 Postgres
```

**Query path 1 — Full image:** CLIP bathroom filter → YOLO detect → crop → embed → query DB → fetch match images from S3.

**Query path 2 — Pre-cropped object:** skip filter/detector → embed → query DB for the selected label.

---

## Repository structure

```
EESI/
├── .env.example          # Copy to .env
├── requirements.txt      # Python dependencies
├── pipeline/             # ML + database query code
├── models/               # YOLO weights (object_detector_best.pt required)
├── app/                  # Electron desktop app — this is what you run
└── examples/             # Optional CLI scripts (not needed for normal use)
```

Key `pipeline/` modules: `core.py` (orchestration), `query.py` (search), `db.py`, `s3.py`, `yolo_detector.py`, `embedder.py`.

---

## Setup (one-time)

**Prerequisites:** Python 3.11+, Node.js 18+, SSH access to GEN EC2, AWS SSO configured.

From the repository root:

```bash
# 1. Python
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# 2. Environment file
cp .env.example .env
# Defaults in .env.example work for GEN dev (DB user eesi, password eesi1234).
# Update EESI_S3_BUCKET if your team uses a different bucket name.

# 3. Node (Electron app)
cd app
npm install
cd ..
```

Ensure `models/object_detector_best.pt` exists. First analysis will download additional model weights from Hugging Face (~several GB).

### Local machine vs EC2

**You run the app on your laptop.** That is the normal workflow for this repo.

**EC2 hosts the database** (and was used to build the reference index). You do **not** run the Electron app on EC2. You only need EC2 access for:

1. **SSH tunnel** — so your laptop can reach the database (see [Run the app](#run-the-app))
2. **Optional admin** — e.g. `sudo -u postgres psql -d eesi` when SSH'd into EC2 for debugging

| | Your laptop | EC2 |
|---|-------------|-----|
| Run Electron app | ✅ Yes | ❌ No |
| SSH tunnel to DB | ✅ Required | ❌ Not needed |
| AWS SSO for S3 | ✅ Required | Only if running scripts there |
| `sudo -u postgres psql` | ❌ | ✅ Optional admin |

Get `<username>`, `<ec2-host>`, and `<aws-profile>` from your GEN administrator.

---

## Run the app

Do this **every time** you want to use EESI.

### Terminal 1 — SSH tunnel (keep open)

Forwards your laptop’s port 5432 to PostgreSQL on EC2:

```bash
ssh -L 5432:localhost:5432 <username>@<ec2-host> -N
```

Background option: add `-f` after `ssh`.

If port 5432 is busy on your Mac, use `-L 15432:localhost:5432` and set `EESI_DB_PORT=15432` in `.env`.

### Terminal 2 — AWS + app

```bash
aws sso login --profile <aws-profile>
export AWS_PROFILE=<aws-profile>

cd /path/to/EESI
source .venv/bin/activate
cd app
npm run electron-dev
```

**Important:** Use the **Electron window** that opens — not the browser tab at localhost:5173.

If you are already inside `app/`, run `npm run electron-dev` only (do not `cd app` again).

### Checklist

Before clicking **Analyze Image**, confirm:

- [ ] Terminal 1: SSH tunnel is running
- [ ] `aws sso login` succeeded (`export AWS_PROFILE=...`)
- [ ] Python venv is activated
- [ ] `.env` exists at repo root

First query may take a few minutes while models load.

---

## Using the app

1. **Upload** an image (PNG, JPG, WEBP).
2. Choose a mode:
   - **Full Image** — auto-detects bathroom objects (YOLO).
   - **Crop + Label** — you already cropped the object; pick the class (toilet, sink, etc.).
3. Click **Analyze Image**.
4. Select a detected object (full-image mode) to view **top matches** with location, similarity %, and reference thumbnails.
5. **Export Results** saves JSON locally.

**Tips:**

- “No objects detected” → try **Crop + Label**, or use a clearer bathroom photo.
- Match images require AWS SSO; re-run `aws sso login` if thumbnails fail to load.
- DB errors → check SSH tunnel and `.env` password (`eesi1234` for dev).

---

## Database schema

Table: **`objects`**

| Column | Description |
|--------|-------------|
| `label` | Object class (13 YOLO classes) |
| `city`, `state`, `country`, `continent` | Geographic metadata |
| `lat`, `long` | Coordinates |
| `image_path` | S3 URI for reference crop |
| `base_clip_embedding` | **Production search column** (1024-d, cosine similarity) |
| `flora_embedding`, `dino_embedding`, `geolora_embedding_e1`–`e4` | Alternate embedding columns |

Queries filter by `label` and rank by pgvector cosine distance (`<=>`, lower = more similar).

**Two ways to connect to Postgres:**

| Method | Password? |
|--------|-----------|
| App / pipeline via tunnel (`localhost:5432`, user `eesi`) | Yes — `EESI_DB_PASSWORD` in `.env` |
| `sudo -u postgres psql -d eesi` on EC2 | No (admin only) |

---

## Models

| Model | Purpose | Location |
|-------|---------|----------|
| **YOLO26s (custom)** | Detect 13 bathroom object classes | `models/object_detector_best.pt` |
| **DFN-CLIP ViT-H/14-378** | Production embeddings (default) | Downloaded via `open_clip` on first run |
| **roomLuxuryAnnotater** | Bathroom scene filter | Hugging Face |
| **Flora / GeoLoRA / DINOv2** | Alternate embedders (optional) | `models/weights-41.pt`, `geolora_checkpoints/` |

**YOLO classes:** bathtub, bidet, brand, floor, mirror, outlet, plant, rug, shower, showerhead, sink, toilet, window.

Production queries use **`base_clip_embedding`** (`EESI_EMBEDDING_COLUMN` in `.env`).

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `password authentication failed for user "eesi"` | Set `EESI_DB_PASSWORD=eesi1234` in `.env`; ensure SSH tunnel is running |
| `connection refused` on port 5432 | Start SSH tunnel (Terminal 1) |
| Match images missing / S3 errors | `aws sso login --profile <aws-profile>` and `export AWS_PROFILE=...` |
| `Electron bridge unavailable` | Use the Electron window, not the browser |
| `cd: no such file or directory: app` | Already in `app/` — run `npm run electron-dev` only |
| Port 5173 in use | `lsof -ti :5173 \| xargs kill -9` |
| Slow first run | Normal — models downloading/loading |

### `.env` reference

| Variable | Default |
|----------|---------|
| `EESI_DB_HOST` | `localhost` (with tunnel) |
| `EESI_DB_PORT` | `5432` |
| `EESI_DB_NAME` / `EESI_DB_USER` | `eesi` |
| `EESI_DB_PASSWORD` | `eesi1234` |
| `EESI_S3_BUCKET` | set in `.env.example` |
| `EESI_EMBEDDING_COLUMN` | `base_clip_embedding` |

---

Developed by Cal Poly Data Science in partnership with GEN.
