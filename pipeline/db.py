# MODULE FOR INSERTING TO DB

import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
from pgvector.psycopg2 import register_vector

# Load .env from repository root (parent of pipeline/)
_REPO_ROOT = Path(__file__).resolve().parent.parent
load_dotenv(_REPO_ROOT / ".env")


def get_connection():
    conn = psycopg2.connect(
        host=os.getenv("EESI_DB_HOST", "localhost"),
        port=int(os.getenv("EESI_DB_PORT", "5432")),
        dbname=os.getenv("EESI_DB_NAME", "eesi"),
        user=os.getenv("EESI_DB_USER", "eesi"),
        password=os.getenv("EESI_DB_PASSWORD", "eesi1234"),
    )
    register_vector(conn)
    return conn


def insert_object(
    label,
    image_path,
    city=None,
    state=None,
    country=None,
    continent=None,
    lat=None,
    long=None,
    caption=None,
    embedding=None,
):
    """Insert a reference object row (ingestion path)."""
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        INSERT INTO objects (
            label, image_path, city, state, country, continent,
            lat, long, caption, base_clip_embedding
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            label,
            image_path,
            city,
            state,
            country,
            continent,
            lat,
            long,
            caption,
            embedding,
        ),
    )

    conn.commit()
    cur.close()
    conn.close()
