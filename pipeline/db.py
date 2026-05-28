# MODULE FOR INSERTING TO DB

import psycopg2
from pgvector.psycopg2 import register_vector
import numpy as np

def get_connection():
    conn = psycopg2.connect(
        host="localhost",
        port=5432,
        dbname="eesi",
        user="eesi",
        password="eesi1234"
    )
    register_vector(conn)
    return conn

def insert_object(label, image_path, city=None, state=None, country=None, 
                  continent=None, lat=None, long=None, caption=None, embedding=None):
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        INSERT INTO objects (label, image_path, city, state, country, continent, lat, long, caption, embedding)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, (label, image_path, city, state, country, continent, lat, long, caption, embedding))
    
    conn.commit()
    cur.close()
    conn.close()