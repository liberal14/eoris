"""
fix_danger_levels.py
────────────────────
Updates existing explosive records in the database to use the correct
danger level classification:
  Level 5 → High explosive filling (Aviation Bomb, Sea Mine, AntiSubmarine Bomb)
  Level 4 → Large destructive munitions (LandMine, Rocket, RPG)
  Level 3 → Suppression / fragmentation (Grenade, Projectile, Mortar Bomb)
  Level 2 → Small arms / initiators (Cartridge, Cartridge Magazine, Fuse)
"""
import os, sys
sys.path.append(os.getcwd())

from database import SessionLocal
from models import ExplosiveItem

CATEGORY_DANGER = {
    "Aviation Bomb":      5,
    "Practice Bomb":      1,  # Inert / training ordnance, no explosive filling
    "Sea Mine":           5,
    "AntiSubmarine Bomb": 5,
    "LandMine":           4,
    "Rocket":             4,
    "RPG":                4,
    "Mortar Bomb":        4,
    "Grenade":            3,
    "Projectile":         3,
    "Fuse":               2,
    "Cartridge":          2,
    "Cartridge Magazine": 2,
}

def fix():
    session = SessionLocal()
    try:
        items = session.query(ExplosiveItem).all()
        updated = 0
        for item in items:
            correct_level = CATEGORY_DANGER.get(item.explosive_type)
            if correct_level is not None and item.danger_level != correct_level:
                print(f"  [UPDATE] '{item.name}' ({item.explosive_type}): {item.danger_level} -> {correct_level}")
                item.danger_level = correct_level
                updated += 1
        session.commit()
        print(f"\nDone. Updated {updated} records.")
    except Exception as e:
        session.rollback()
        print(f"Error: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    fix()
