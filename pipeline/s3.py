# MODULE FOR SENDING IMAGES TO S3

import boto3
import io
from urllib.parse import urlparse
from PIL import Image
import os

BUCKET = "eesi-students-368003222772"

_s3_client = None

# get the s3 client
def get_client():
    global _s3_client
    if _s3_client is None:
        _s3_client = boto3.client("s3")
    return _s3_client

# parse the image path to s3
def parse_s3_uri(s3_uri: str):
    parsed = urlparse(s3_uri)
    if parsed.scheme != "s3":
        raise ValueError(f"Expected s3:// URI, got {s3_uri}")
    bucket = parsed.netloc
    key = parsed.path.lstrip("/")
    return bucket, key

# upload an image to s3
def upload_image(image, s3_key):
    client = get_client()
    buffer = io.BytesIO()
    image = image.convert("RGB")
    image.save(buffer, format="JPEG")
    buffer.seek(0)
    client.upload_fileobj(buffer, BUCKET, s3_key)
    return f"s3://{BUCKET}/{s3_key}"

# check if object exists before retrieving
def object_exists(s3_path):
    bucket, key = parse_s3_uri(s3_path)
    client = get_client()
    try:
        client.head_object(Bucket=bucket, Key=key)
        return True
    except client.exceptions.NoSuchKey:
        return False
    except Exception:
        return False

# retrieve image from s3
def retrieve_image(s3_path):
    bucket, key = parse_s3_uri(s3_path)

    client = get_client()
    buffer = io.BytesIO()
    client.download_fileobj(bucket, key, buffer)
    buffer.seek(0)

    image = Image.open(buffer)
    image.load()
    return image

# delete image from s3
def delete_image(s3_path):
    bucket, key = parse_s3_uri(s3_path)
    client = get_client()
    client.delete_object(Bucket=bucket, Key=key)

# count the number of images in s3
def count_images(prefix=""):
    client = get_client()
    paginator = client.get_paginator("list_objects_v2")
    total = 0
    for page in paginator.paginate(Bucket=BUCKET, Prefix=prefix):
        total += page.get("KeyCount", 0)
    return total