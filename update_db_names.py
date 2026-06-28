import os
import sys

# Add current directory to path
sys.path.append(os.getcwd())

from database import SessionLocal
from models import ExplosiveItem

def update_item(session, filename, new_name, new_type, new_desc, new_danger):
    url = f"/images/{filename}"
    item = session.query(ExplosiveItem).filter(ExplosiveItem.image_url == url).first()
    if item:
        item.name = new_name
        item.explosive_type = new_type
        item.description = new_desc
        item.danger_level = new_danger
        print(f"Updated: {filename} -> {new_name}")
    else:
        print(f"Not found: {filename}")

def main():
    session = SessionLocal()

    updates = [
        ("download.jpg", "Massive Ordnance Penetrator / Heavy Bomb", "bomb", "A very large, heavy aerial bomb characterized by its massive size and white stripe markings, designed for deep penetration.", 5),
        ("download (1).jpg", "FAB-500 Series Aerial Bomb", "bomb", "A Soviet/Russian-designed 500 kg general-purpose air-dropped bomb with a streamlined grey body.", 4),
        ("download (2).jpg", "General Purpose Aerial Bomb (Red Nose)", "bomb", "A large grey aerial bomb featuring a distinctive red nose cone and rear fin assembly, typically used for precision or general-purpose strikes.", 4),
        ("8WonafKZanpD29WACM3dCKC6jq9QBBc0JEyVcZyD.jpg", "AN-M30A1 100-lb GP Bomb", "bomb", "A US 100-pound general-purpose explosive bomb from the WWII era, marked with a yellow high-explosive identifier band.", 4),
        ("TD58AoDcPQKTk0mulPhhJbWEpTx55HxktBJoIYtj.jpg", "Vintage Fin-Stabilized Ordnance", "bomb", "An older, rusted aerial bomb or large mortar projectile with a box fin assembly at the rear.", 3),
        ("ritgEPNjXScuZGx3IBZOHtE9isdZObCicz1uIh4M.jpg", "Modern Low-Drag GP Bomb", "bomb", "A streamlined, low-drag aerial bomb painted in standard grey, designed for carriage on high-speed aircraft.", 4),
        ("sGgDmah0XygkNI0btMmkmlZh3ysAPWq3G5bqVpj0.jpg", "Small Fragmentation Bomb", "bomb", "A small air-dropped bomb or submunition featuring a black nose section and compact tail fins.", 3),
    ]

    for filename, name, etype, desc, danger in updates:
        update_item(session, filename, name, etype, desc, danger)

    session.commit()
    session.close()
    print("Database update complete.")

if __name__ == "__main__":
    main()
