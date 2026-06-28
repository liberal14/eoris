"""
seed_images_folder.py
─────────────────────
Bulk-imports every image found in the ./images/ folder into the
explosives database.  For each file it:
  • Derives a clean display name from the filename
  • Guesses explosive_type from keywords in the filename
  • Assigns a danger_level heuristic
  • Generates a short description
  • Computes pHash + ResNet18 feature vector for visual search
  • Skips files already present (by image_url) to allow reruns
"""

import os, sys, re
sys.path.append(os.getcwd())

from database import SessionLocal
from models import ExplosiveItem
from image_logic import get_image_phash, get_feature_vector

# ── Supported image extensions ──────────────────────────────────────────────
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".gif"}

IMAGES_DIR  = os.path.join(os.getcwd(), "images")
URL_PREFIX  = "/images"   # FastAPI static mount path

# ── Keyword maps ─────────────────────────────────────────────────────────────
TYPE_KEYWORDS = {
    "rocket":   ["rocket", "hydra", "sneb", "s8", "s-8", "s5", "r-60", "r-73", "r-77",
                 "amraam", "atgm", "r-27", "r-60", "r-73"],
    "bomb":     ["bomb", "fab", "ofab", "mk", "mark", "m117", "m41", "m88", "bafg",
                 "be-500", "be500", "gbu", "blu", "agm-62", "walleye", "durandal",
                 "belouga", "a-n-m", "cbu", "4000lb", "3kg", "20lb"],
    "practice_bomb": ["practice", "bdu", "training bomb", "inert"],
    "grenade":  ["grenade", "frag", "smoke", "gren"],
    "mine":     ["mine", "pmn", "tm-", "at mine", "ap mine"],
    "projectile": ["projectile", "shell", "round", "cartridge", "mortar"],
}

DANGER_KEYWORDS = {
    5: ["cluster", "thermobaric", "fuel-air", "cbu", "submunition"],
    4: ["bomb", "fab", "ofab", "guided", "agm", "gbu", "4000"],
    3: ["rocket", "amraam", "atgm", "hydra", "sneb"],
    2: ["grenade", "mortar", "projectile", "shell"],
    1: ["cartridge", "fuse", "smoke", "practice", "bdu", "inert"],
}


def clean_name(filename: str) -> str:
    """Turn a filename into a readable display name."""
    stem = os.path.splitext(filename)[0]
    # Remove trailing numbers that look like download indices
    stem = re.sub(r'\s*\(\d+\)$', '', stem)
    # Replace hyphens/underscores with spaces, title-case
    name = stem.replace("-", " ").replace("_", " ").strip()
    return name.title()


def guess_type(filename: str) -> str:
    lower = filename.lower()
    for etype, keywords in TYPE_KEYWORDS.items():
        if any(kw in lower for kw in keywords):
            return etype
    return "other"


def guess_danger(filename: str, etype: str) -> int:
    lower = filename.lower()
    for level in sorted(DANGER_KEYWORDS.keys(), reverse=True):
        if any(kw in lower for kw in DANGER_KEYWORDS[level]):
            return level
    # Fallback by type
    return {"bomb": 4, "rocket": 3, "mine": 4,
            "grenade": 3, "projectile": 2, "practice_bomb": 1, "other": 2}.get(etype, 2)


def build_description(name: str, etype: str) -> str:
    type_labels = {
        "bomb":       "an aerial bomb",
        "rocket":     "an unguided/guided rocket munition",
        "mine":       "a land or anti-vehicle mine",
        "grenade":    "a hand grenade or grenade-type munition",
        "projectile": "an artillery/mortar projectile",
        "other":      "a classified ordnance item",
    }
    label = type_labels.get(etype, "an ordnance item")
    return (f"{name} is {label}. "
            f"Imported from the local image library. "
            f"Verify specifications against official EOD references before operational use.")


def run():
    if not os.path.isdir(IMAGES_DIR):
        print(f"ERROR: images folder not found at {IMAGES_DIR}")
        sys.exit(1)

    files = [f for f in os.listdir(IMAGES_DIR)
             if os.path.splitext(f)[1].lower() in IMAGE_EXTS]
    print(f"Found {len(files)} image files in ./images/\n")

    session = SessionLocal()
    inserted = 0
    skipped  = 0
    errors   = 0

    for filename in sorted(files):
        url = f"{URL_PREFIX}/{filename}"

        # Skip if already imported
        existing = session.query(ExplosiveItem).filter(
            ExplosiveItem.image_url == url
        ).first()
        if existing:
            print(f"  [SKIP]  {filename}  (already in DB as '{existing.name}')")
            skipped += 1
            continue

        file_path = os.path.join(IMAGES_DIR, filename)
        name      = clean_name(filename)
        etype     = guess_type(filename)
        danger    = guess_danger(filename, etype)
        desc      = build_description(name, etype)

        print(f"  [IMPORT] {filename}")
        print(f"           Name={name!r}  Type={etype}  Danger={danger}")

        try:
            phash = get_image_phash(file_path)
            fvec  = get_feature_vector(file_path)
        except Exception as e:
            print(f"           ERROR computing features: {e}")
            errors += 1
            continue

        item = ExplosiveItem(
            name             = name,
            explosive_type   = etype,
            danger_level     = danger,
            description      = desc,
            image_url        = url,
            image_hash       = phash,
            feature_vector   = fvec,
            metadata_signature = {"source": "images_folder", "original_filename": filename},
        )
        session.add(item)
        inserted += 1

    session.commit()
    session.close()

    print(f"\n{'='*50}")
    print(f"  Inserted : {inserted}")
    print(f"  Skipped  : {skipped}  (already existed)")
    print(f"  Errors   : {errors}")
    print(f"{'='*50}")


if __name__ == "__main__":
    run()
