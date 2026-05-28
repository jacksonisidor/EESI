# MODULE FOR FILTERING OUT NON-BATHROOM IMAGES

from transformers import pipeline
from PIL import Image 
import torch

# initialize constants
MODEL_ID = "strollingorange/roomLuxuryAnnotater"
LABELS = [
    "a photo of a bathroom",
    "a photo of a bedroom",
    "a photo of a kitchen",
    "a photo of a foyer",
    "a photo of a living room",
    "a photo of a dining room",
    "a photo outside a house"
]

# initialize classifier to none for first use
_classifier = None

# download the classifier if first time, otherwise use what is downloaded
def get_classifier():
    global _classifier
    if _classifier is None:
        # Explicitly set device to 0 (the T4 GPU)
        device = 0 if torch.cuda.is_available() else -1
        _classifier = pipeline("zero-shot-image-classification", model=MODEL_ID, device=device)
    return _classifier

# main function for classifying bathrooms
def is_bathroom(image: Image.Image):
    
    # get and use the classifer
    classifier = get_classifier()
    image = image.convert("RGB")
    result = classifier(image, candidate_labels=LABELS)

    # check if we should return bathroom or not
    most_confident = result[0]
    if most_confident['label'] == 'a photo of a bathroom' and most_confident['score'] > 0.5:
        return True
    else:
        return False
