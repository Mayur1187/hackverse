from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageChops, ImageEnhance
import imagehash
import pytesseract


def extract_advanced_features(image_path: Path) -> np.ndarray:
    base_features = extract_image_features(image_path)

    img = Image.open(image_path).convert("L")

    # 🔁 Perceptual Hash
    phash = imagehash.phash(img)
    phash_num = float(int(str(phash), 16) % 1e6)

    # 🧪 ELA Score
    ela_score = _ela_score(image_path)

    # 🔤 OCR Score
    ocr_score = _ocr_consistency_score(image_path)

    return np.concatenate([
        base_features,
        np.array([phash_num, ela_score, ocr_score], dtype=np.float32)
    ])


# ---------- YOUR EXISTING FUNCTIONS ----------
def extract_image_features(image_path: Path) -> np.ndarray:
    image = cv2.imread(str(image_path))
    if image is None:
        raise ValueError(f"Could not read image: {image_path}")

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    gray = cv2.resize(gray, (512, 512))
    equalized = cv2.equalizeHist(gray)

    edges = cv2.Canny(equalized, 80, 180)
    blurred = cv2.GaussianBlur(equalized, (5, 5), 0)
    residual = cv2.absdiff(equalized, blurred)
    laplacian = cv2.Laplacian(equalized, cv2.CV_64F)

    features = []
    features.extend(_stats(equalized))
    features.extend(_stats(edges.astype(np.float32)))
    features.extend(_stats(residual.astype(np.float32)))
    features.extend(_stats(np.abs(laplacian).astype(np.float32)))
    features.extend(_frequency_features(equalized))

    return np.array(features, dtype=np.float32)


def _stats(values):
    flat = values.ravel()
    return [float(np.mean(flat)), float(np.std(flat))]


def _frequency_features(gray):
    dct = cv2.dct(gray.astype(np.float32) / 255.0)
    return [float(np.mean(dct)), float(np.std(dct))]


# ---------- NEW FUNCTIONS ----------
def _ela_score(image_path: Path) -> float:
    original = Image.open(image_path)
    temp = "temp.jpg"

    original.save(temp, "JPEG", quality=90)
    compressed = Image.open(temp)

    ela = ImageChops.difference(original, compressed)
    ela = ImageEnhance.Brightness(ela).enhance(10)

    return float(np.mean(np.array(ela)) / 255.0)


def _ocr_consistency_score(image_path: Path) -> float:
    img = cv2.imread(str(image_path))
    text = pytesseract.image_to_string(img)

    score = 0
    if "CERT" in text:
        score += 1
    if any(char.isdigit() for char in text):
        score += 1
    if len(text) > 20:
        score += 1

    return score / 3.0