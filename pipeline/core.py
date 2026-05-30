# CORE PIPELINE MODULE

'''
This module performs the shared steps between scraping and investigator usage:
clip_filter -> yolo -> cropping -> embedding

Afterwards, the two paths diverge in ingest.py and query.py
'''

# import all the modules
from .clip_filter import is_bathroom
from .yolo_detector import detect_objects
from .cropper import crop_detections
# from .captioner import generate_captions
from .embedder import generate_dino_embedding, generate_flora_embedding, generate_base_clip_embedding, generate_geolora3_embedding
from PIL import Image


# performs all core steps of processing a FULL image
def process_image(image):

    # step 1: filter out non-bathrooms
    if not is_bathroom(image):
        return None

    # step 2: detect objects
    detections = detect_objects(image)
    if not detections:
        return None
    
    # step 3: crop detected objects
    cropped_objects = crop_detections(image, detections)
    if not cropped_objects:
        return None

    # step 4: generate captions for each object
    #for obj in cropped_objects:
        #obj['caption'] = generate_captions(obj['crop'], obj['label'])

    # step 5: generate embeddings for each object
    for obj in cropped_objects:
        obj['embedding'] = generate_base_clip_embedding(obj['crop'])

    return cropped_objects


# generates an embedding for pre-cropped images with a known label
def process_crop(image, label):
    image = image.convert("RGB")
    embedding = generate_base_clip_embedding(image)
    return [{
        'label': label,
        'crop': image,
        'embedding': embedding
    }]
