# MODULE FOR FINISHING SCRAPING PIPELINE

'''
This module uses the shared steps in core.py, then continues 
the additional steps for ingesting the scraped images
'''

from .core import process_image
from .s3 import upload_image
from .db import insert_object

def store_image(image, base_key, metadata):
    
    # Step 1: run through core pipeline
    cropped_objects = process_image(image)
    if not cropped_objects:
        return None

    # loop through each cropped object for next steps
    for i, obj in enumerate(cropped_objects):

        # Step 2: send cropped image to S3 and store path
        obj_key = f"{base_key}/{obj['label']}_{i}.jpg"
        s3_path = upload_image(obj['crop'], obj_key)

        # Step 3: insert rows into DB for detected objects
        insert_object(
            label=obj['label'],
            image_path=s3_path,
            city=metadata.get('city'),
            state=metadata.get('state'),
            country=metadata.get('country'),
            continent=metadata.get('continent'),
            lat=metadata.get('lat'),
            long=metadata.get('long'),
            caption=obj.get('caption'),
            embedding=obj.get('embedding')
        )

    return cropped_objects