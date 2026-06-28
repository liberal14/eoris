# seed_db.py
"""Utility script to unzip the CTX‑UXO archive and seed the PostgreSQL database
with COCO‑style annotation data.
"""
import os
import json
import zipfile
from pathlib import Path
from datetime import datetime

from sqlalchemy.orm import Session

# Local project imports
from database import SessionLocal, engine, Base
from models import ExplosiveItem

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
PROJECT_ROOT = Path(__file__).parent
ZIP_PATH = PROJECT_ROOT / "CTX-UXO.zip"
EXTRACT_DIR = PROJECT_ROOT / "extracted"
COCO_JSON_FILES = [
    EXTRACT_DIR / "coco_labels" / "coco_train.json",
    EXTRACT_DIR / "coco_labels" / "coco_val.json",
    EXTRACT_DIR / "coco_labels" / "coco_test.json",
]
IMAGES_DIR = EXTRACT_DIR / "images"

# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------

def unzip_archive(zip_path: Path, extract_to: Path) -> None:
    """Extract ``zip_path`` into ``extract_to`` using ``zipfile``.
    ``extract_to`` will be created if it does not exist.
    """
    if not zip_path.is_file():
        raise FileNotFoundError(f"Archive not found: {zip_path}")
    extract_to.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_to)
    print(f"Extracted {zip_path.name} to {extract_to}")


def load_coco_json(json_path: Path) -> dict:
    """Load a COCO JSON file and return the parsed dict."""
    with json_path.open("r", encoding="utf-8") as f:
        return json.load(f)


# Category mapping based on CTX-UXO dataset
CATEGORY_MAP = {
    0: "AntiSubmarine Bomb",
    1: "Aviation Bomb",
    2: "Cartridge",
    3: "Cartridge Magazine",
    4: "Fuse",
    5: "Grenade",
    6: "LandMine",
    7: "Mortar Bomb",
    8: "Projectile",
    9: "RPG",
    10: "Rocket",
    11: "Sea Mine"
}

def seed_from_coco(session: Session, coco_data: dict) -> int:
    """Insert records into the ``explosives`` table.

    For each image entry we create a single ``ExplosiveItem`` row. The
    ``metadata_signature`` column stores the full image dictionary together with
    the list of associated annotations (if any).
    """
    inserted = 0
    # Map image_id -> list of annotations
    ann_by_image = {}
    for ann in coco_data.get("annotations", []):
        img_id = ann.get("image_id")
        ann_by_image.setdefault(img_id, []).append(ann)

    for img in coco_data.get("images", []):
        image_id = img.get("id")
        file_name = img.get("file_name")
        image_path = f"/extracted/images/{file_name}"
        image_annotations = ann_by_image.get(image_id, [])
        
        # Determine category and name
        category_name = "Unknown UXO"
        if image_annotations:
            cat_id = image_annotations[0].get("category_id")
            category_name = CATEGORY_MAP.get(cat_id, f"Category {cat_id}")
        
        # Better name format
        name = f"{category_name} ({Path(file_name).stem})"
        
        # Create a basic description
        description = f"Industrial unexploded ordnance (UXO) categorized as {category_name}. Source: CTX-UXO Dataset."
        
        # Assign danger level based on category and role
        # Level 5: High explosive filling (large blast / area destruction)
        # Level 4: Large destructive munitions (anti-tank, rockets, mines)
        # Level 3: Suppression / fragmentation (grenades, projectiles, mortars)
        # Level 2: Small arms, initiators (cartridges, fuses)
        CATEGORY_DANGER = {
            "Aviation Bomb":      5,  # High explosive filling
            "Practice Bomb":      1,  # Inert / training ordnance, no explosive filling
            "Sea Mine":           5,  # High explosive filling
            "AntiSubmarine Bomb": 5,  # High explosive filling
            "LandMine":           4,  # Anti-personnel/vehicle, buried explosive
            "Rocket":             4,  # Tactical bombardment with warhead
            "RPG":                4,  # Anti-tank shaped charge
            "Mortar Bomb":        4,  # Indirect fire support with explosive warhead
            "Grenade":            3,  # Close-quarters personnel suppression
            "Projectile":         3,  # Artillery/mortar projectile
            "Fuse":               2,  # Detonation trigger only
            "Cartridge":          2,  # Small arms ammunition
            "Cartridge Magazine":  2,  # Ammunition holder
        }
        danger_level = CATEGORY_DANGER.get(category_name, 3)  # Default to 3 for unknown
        
        item = ExplosiveItem(
            name=name,
            explosive_type=category_name,
            description=description,
            danger_level=danger_level,
            metadata_signature={"image": img, "annotations": image_annotations},
            image_hash=None,
            image_url=image_path,
            created_at=datetime.utcnow(),
        )
        session.add(item)
        inserted += 1
    session.commit()
    return inserted

# ---------------------------------------------------------------------------
# Main Execution Flow
# ---------------------------------------------------------------------------

def main() -> None:
    if not any(p.exists() for p in COCO_JSON_FILES):
        print("Unzipping archive ...")
        unzip_archive(ZIP_PATH, EXTRACT_DIR)
    else:
        print("Archive already extracted - skipping unzip.")

    session = SessionLocal()
    total_inserted = 0
    try:
        for json_file in COCO_JSON_FILES:
            if not json_file.is_file():
                print(f"Missing JSON file: {json_file.name} – skipping")
                continue
            print(f"Loading {json_file.name} ...")
            coco_data = load_coco_json(json_file)
            count = seed_from_coco(session, coco_data)
            print(f"Inserted {count} records from {json_file.name}")
            total_inserted += count
    finally:
        session.close()
    print(f"Finished – total rows inserted: {total_inserted}")

if __name__ == "__main__":
    main()
