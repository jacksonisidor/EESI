# MODULE FOR CROPPING OBJECTS

from PIL import Image

# crop a single object from an image at given coordinates
def crop_from_bbox(image: Image.Image, bbox_xyxy):
    image = image.convert("RGB")
    width, height = image.size

    x1, y1, x2, y2 = bbox_xyxy

    # clip to image bounds
    x1 = max(0, min(int(round(x1)), width))
    y1 = max(0, min(int(round(y1)), height))
    x2 = max(0, min(int(round(x2)), width))
    y2 = max(0, min(int(round(y2)), height))

    # reject invalid boxes
    if x2 <= x1 or y2 <= y1:
        return None

    return image.crop((x1, y1, x2, y2))

# crop all detected objects from YOLO
def crop_detections(image: Image.Image, detections):
    cropped_objects = []

    for det in detections:
        crop = crop_from_bbox(image, det["bbox_xyxy"])
        if crop is None:
            continue

        cropped_objects.append({
            "label": det["label"],
            "confidence": det["confidence"],
            "bbox_xyxy": det["bbox_xyxy"],
            "crop": crop
        })

    return cropped_objects