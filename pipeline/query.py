# MODULE FOR FINISHING QUERY PIPELINE

'''
This module uses the shared steps in core.py, then continues 
the additional steps for returning matches to the investigator
'''

from .core import process_image, process_crop
from .db import get_connection 
from .s3 import retrieve_image
import numpy as np 
import io
import base64

# if there are duplicate images in the reference DB, we don't want to return both
def deduplicate_results(results, threshold=0.001):
    seen_distances = []
    deduped = []
    for r in results:
        too_close = any(abs(r['distance'] - d) < threshold for d in seen_distances)
        if not too_close:
            seen_distances.append(r['distance'])
            deduped.append(r)
    return deduped

# get matches for ONE object from db using embeddings
def query_db(embedding, label, k):

    fetch_k = k * 3 # fetch more to account for deduplication
    
    # establish connection to postgres
    conn = get_connection()
    cur = conn.cursor()

    # query top k matches for this object
    ## <=> means cosine distance
    cur.execute(
        """ 
        SELECT label, image_path, city, state, country, continent,
            lat, long, base_clip_embedding <=> %s::vector AS distance
        FROM objects 
        WHERE label = %s
        ORDER BY distance
        LIMIT %s
        """, (embedding.tolist(), label, fetch_k)
    )

    rows = cur.fetchall()
    cur.close()
    conn.close()

    # store matches as a list of jsons 
    results = []
    for row in rows:
        image_path = row[1]
        image_data = None
        image_error = None
        try:
            image = retrieve_image(image_path)
            buffer = io.BytesIO()
            image.convert('RGB').save(buffer, format='JPEG')
            image_data = base64.b64encode(buffer.getvalue()).decode('ascii')
        except Exception as e:
            image_error = str(e)

        results.append({
            'label': row[0],
            'image_path': image_path,
            'image_data': image_data,
            'image_retrieval_error': image_error,
            'city': row[2],
            'state': row[3],
            'country': row[4],
            'continent': row[5],
            'lat': row[6],
            'long': row[7],
            'distance': row[8]
        })

    results = deduplicate_results(results)
    return results[:k]


# PATH 1: if given a full image
def query_from_image(image, k=5):
    
    # run through core pipeline (detecting objects, generating embeddings)
    objects = process_image(image)
    if not objects:
        return None
    
    # query for matches for each object individually
    all_results = {}
    for obj in objects:
        matches = query_db(obj['embedding'], obj['label'], k)
        all_results[obj['label']] = matches
    
    return all_results

# PATH 2: if given a pre-cropped, pre-labeled image
def query_from_crop(image, label, k=5):
    
    # generate embedding for this crop
    objects = process_crop(image, label)
    obj = objects[0]

    # query for matches for just this one object
    results = query_db(obj['embedding'], label, k)

    return results