from PIL import Image
from PIL.ExifTags import TAGS
import imagehash
import os
import json
import numpy as np

# ─────────────────────────────────────────────────────────────────────────────
# Feature extraction strategy (best → fallback):
#
#   1. ResNet18 deep features  (torch + torchvision)  – semantic, 512-dim
#   2. HOG features            (scikit-image)          – shape-based, ~8100-dim
#   3. Multi-hash combo        (imagehash only)        – last resort
#
# The app works at whichever level is available.
# ─────────────────────────────────────────────────────────────────────────────

# ── Level 1: ResNet18 deep features ──────────────────────────────────────────
_torch_model     = None
_torch_transform = None
_torch_available = None   # None = not yet tested

def _get_torch_model():
    global _torch_model, _torch_transform, _torch_available
    if _torch_available is not None:
        return _torch_model, _torch_transform

    try:
        import torch
        import torchvision.models as tv_models
        import torchvision.transforms as tv_transforms

        base = tv_models.resnet18(weights=tv_models.ResNet18_Weights.DEFAULT)
        _torch_model = torch.nn.Sequential(*list(base.children())[:-1])
        _torch_model.eval()

        _torch_transform = tv_transforms.Compose([
            tv_transforms.Resize(256),
            tv_transforms.CenterCrop(224),
            tv_transforms.ToTensor(),
            tv_transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            ),
        ])
        _torch_available = True
        print("[image_logic] ResNet18 (torch) loaded - using deep feature matching.")
    except ImportError:
        _torch_available = False
        print("[image_logic] WARNING: torch not available - falling back to HOG features.")

    return _torch_model, _torch_transform


def _extract_resnet_vector(image_path):
    """512-dim ResNet18 embedding. Returns list or None."""
    try:
        import torch
        model, transform = _get_torch_model()
        if not model:
            return None
        img    = Image.open(image_path).convert("RGB")
        tensor = transform(img).unsqueeze(0)
        with torch.no_grad():
            features = model(tensor)
        return features.squeeze().numpy().tolist()
    except Exception as e:
        print(f"[image_logic] ResNet error: {e}")
        return None


# ── Level 2: HOG (Histogram of Oriented Gradients) features ──────────────────
_skimage_available = None

def _check_skimage():
    global _skimage_available
    if _skimage_available is not None:
        return _skimage_available
    try:
        from skimage.feature import hog  # noqa
        _skimage_available = True
        print("[image_logic] scikit-image available - using HOG shape features.")
    except ImportError:
        _skimage_available = False
        print("[image_logic] scikit-image not available - using multi-hash fallback.")
    return _skimage_available


def _extract_hog_vector(image_path):
    """HOG feature vector (~8100-dim). Returns list or None."""
    try:
        from skimage.feature import hog
        from skimage.transform import resize as sk_resize
        from skimage.color import rgb2gray
        import numpy as np

        img = Image.open(image_path).convert("RGB")
        img_arr = np.array(img)

        # Resize to fixed size so vectors are always the same length
        img_resized = sk_resize(img_arr, (128, 128), anti_aliasing=True)
        gray        = rgb2gray(img_resized)

        features = hog(
            gray,
            orientations=9,
            pixels_per_cell=(8, 8),
            cells_per_block=(2, 2),
            feature_vector=True,
        )
        return features.tolist()
    except Exception as e:
        print(f"[image_logic] HOG error: {e}")
        return None


# ── Level 3: Multi-hash combo ────────────────────────────────────────────────
def _extract_multi_hash_vector(image_path):
    """
    Concatenate four imagehash fingerprints into one flat binary vector.
    Less semantic than ResNet/HOG but better than a single pHash.
    """
    try:
        img = Image.open(image_path).convert("RGB")
        hashes = [
            imagehash.phash(img),    # perceptual
            imagehash.dhash(img),    # difference
            imagehash.whash(img),    # wavelet
            imagehash.average_hash(img), # average
        ]
        # Each hash is 64 bits; combine into a 256-element binary list
        combined = []
        for h in hashes:
            combined.extend([int(b) for b in bin(int(str(h), 16))[2:].zfill(64)])
        return combined
    except Exception as e:
        print(f"[image_logic] Multi-hash error: {e}")
        return None


# ── Public API ────────────────────────────────────────────────────────────────

def get_feature_vector(image_path):
    """
    Returns the best available feature vector for image_path.

    Priority:
      1. ResNet18 deep features  (requires torch)
      2. HOG features            (requires scikit-image)
      3. Multi-hash combo        (requires only imagehash – always available)
    """
    # Try torch first
    if _torch_available is None:
        _get_torch_model()

    if _torch_available:
        vec = _extract_resnet_vector(image_path)
        if vec is not None:
            return vec

    # Try scikit-image HOG
    if _check_skimage():
        vec = _extract_hog_vector(image_path)
        if vec is not None:
            return vec

    # Last resort: multi-hash
    return _extract_multi_hash_vector(image_path)


def cosine_similarity(vec_a, vec_b):
    """
    Cosine similarity in [0, 1].  1.0 = identical direction (best match).
    Works for vectors of any length as long as both are the same.
    """
    if len(vec_a) != len(vec_b):
        # Vectors from different extraction methods – not comparable
        return 0.0
    a      = np.array(vec_a, dtype=np.float32)
    b      = np.array(vec_b, dtype=np.float32)
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return float(np.dot(a, b) / (norm_a * norm_b))


# ── Existing helpers (unchanged) ─────────────────────────────────────────────

def get_image_metadata(image_path):
    """Extracts interesting EXIF tags from an image."""
    try:
        img      = Image.open(image_path)
        exif_data = img._getexif()
        metadata = {}
        if exif_data:
            for tag_id, value in exif_data.items():
                tag = TAGS.get(tag_id, tag_id)
                if isinstance(value, bytes):
                    try:
                        value = value.decode()
                    except Exception:
                        value = str(value)
                metadata[tag] = str(value)
        return metadata
    except Exception as e:
        print(f"[image_logic] EXIF error: {e}")
        return {}


def get_image_phash(image_path):
    """Calculates the perceptual hash of an image."""
    try:
        img = Image.open(image_path)
        return str(imagehash.phash(img))
    except Exception as e:
        print(f"[image_logic] pHash error: {e}")
        return None


def compare_hashes(hash1, hash2, threshold=10):
    """Returns True if Hamming distance between two pHashes ≤ threshold."""
    if not hash1 or not hash2:
        return False
    h1 = imagehash.hex_to_hash(hash1)
    h2 = imagehash.hex_to_hash(hash2)
    return (h1 - h2) <= threshold
