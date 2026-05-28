# MODULE FOR DETECTING OBJECTS

import ultralytics
from ultralytics import YOLO

ultralytics.checks = lambda: None  
from pathlib import Path

import numpy as np
import torch
from PIL import Image

# access the best model we found during YOLO training
MODEL_PATH = Path(__file__).resolve().parent.parent / "models" / "object_detector_best.pt"

# initialize detector to none for first use
_detector = None

# download the detector if first time, otherwise use what is downloaded
def get_detector():
    device = 'cuda' if torch.cuda.is_available() else 'mps' if torch.backends.mps.is_available() else 'cpu'
    global _detector
    if _detector is None:
        _detector = YOLO(MODEL_PATH, verbose=False)
        _detector.to(device) # Ensure YOLO moves to GPU but can still run locally when no GPU available
    return _detector

def detect_objects(image: Image.Image, confidence: float = 0.3):
    detector = get_detector()
    image = image.convert("RGB")
    image_array = np.array(image)

    results = detector(image_array, conf=confidence, verbose=False)
    result = results[0]

    detections = []
    names = result.names

    if result.boxes is not None:
        for box in result.boxes:
            detections.append({
                "label": names[int(box.cls[0])],
                "confidence": float(box.conf[0]),
                "bbox_xyxy": box.xyxy[0].tolist()
            })

    return detections