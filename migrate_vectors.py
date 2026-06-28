"""
Migration: Backfill feature_vector for existing DB records
==========================================================
Run AFTER add_feature_vector_column.py to generate deep feature vectors
for all explosive items that were added before this upgrade.

    python migrate_vectors.py

Progress is shown per record. Already-processed rows (non-NULL vectors) are skipped.
"""

import os
import json
from dotenv import load_dotenv

load_dotenv()

# ── Database ──────────────────────────────────────────────────────────────────
from database import SessionLocal
from models import ExplosiveItem
from image_logic import get_feature_vector

def main():
    db = SessionLocal()

    try:
        items = db.query(ExplosiveItem).all()
        total   = len(items)
        updated = 0
        skipped = 0
        failed  = 0

        print(f"\n{'='*55}")
        print(f"  Backfill feature vectors – {total} records found")
        print(f"{'='*55}\n")

        for idx, item in enumerate(items, start=1):
            prefix = f"[{idx}/{total}] '{item.name}'"

            # Skip rows that already have a vector
            if item.feature_vector is not None:
                print(f"{prefix}: already has a vector – skipping.")
                skipped += 1
                continue

            # Build the local file path from the stored URL  e.g. /uploads/abc.jpg
            if not item.image_url:
                print(f"{prefix}: no image_url – skipping.")
                skipped += 1
                continue

            # image_url is like /uploads/filename.jpg  or /extracted/...
            rel_path = item.image_url.lstrip("/")
            file_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                rel_path.replace("/", os.sep)
            )

            if not os.path.exists(file_path):
                print(f"{prefix}: file not found at '{file_path}' – skipping.")
                skipped += 1
                continue

            print(f"{prefix}: extracting features from '{file_path}' ...", end=" ", flush=True)
            vector = get_feature_vector(file_path)

            if vector is None:
                print("FAILED (model or file error).")
                failed += 1
                continue

            item.feature_vector = vector
            db.commit()
            print(f"OK  (vector dim={len(vector)})")
            updated += 1

        print(f"\n{'='*55}")
        print(f"  Done.  Updated={updated}  Skipped={skipped}  Failed={failed}")
        print(f"{'='*55}\n")

    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] Migration aborted: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    main()
