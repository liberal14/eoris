import os
import sys
from sqlalchemy.orm import Session

# Add current directory to path
sys.path.append(os.getcwd())

from database import SessionLocal
from models import ExplosiveItem

# Typical Technical Specifications Mapping
TECH_SPECS_MAP = {
    "Aviation Bomb": {
        "weight": "250 - 1000 kg",
        "origin": "USA, Russia, Germany",
        "ignition": "Impact / Proximity Fuze",
        "role": "Air-to-ground tactical strike",
        "usage": "Deployed from aircraft to destroy hardened structures or large area targets."
    },
    "Practice Bomb": {
        "weight": "2.5 - 25 kg",
        "origin": "USA, UK, NATO",
        "ignition": "Spotting charge only (smoke marker)",
        "role": "Aircrew bombing practice and training",
        "usage": "Inert training ordnance replicating the aerodynamics of live bombs. Contains no explosive filling. May include a small spotting charge to mark impact point."
    },
    "Mortar Bomb": {
        "weight": "1.5 - 15 kg",
        "origin": "Russia, USA, UK, China",
        "ignition": "Impact (Point Detonating)",
        "role": "Indirect fire support",
        "usage": "Fired from mortar tubes for high-angle trajectory fire in infantry support."
    },
    "LandMine": {
        "weight": "2 - 10 kg",
        "origin": "Russia, China, Italy, USA",
        "ignition": "Pressure / Tripwire / Magnetic",
        "role": "Area denial and anti-access",
        "usage": "Buried or surface-laid to disable vehicles (anti-tank) or personnel (anti-personnel)."
    },
    "Grenade": {
        "weight": "0.3 - 0.6 kg",
        "origin": "Worldwide / Local Manufactures",
        "ignition": "Time-delay (Pyro-fused)",
        "role": "Close-quarters personnel suppression",
        "usage": "Hand-thrown or launched for fragmentation and blast effects against infantry."
    },
    "Projectile": {
        "weight": "5 - 50 kg",
        "origin": "USA, Russia, China, France",
        "ignition": "Impact / Time / Proximity",
        "role": "Artillery bombardment",
        "usage": "Large-caliber ammunition fired from howitzers or field guns."
    },
    "RPG": {
        "weight": "2 - 5 kg",
        "origin": "Russia (Soviet-era heritage)",
        "ignition": "Impact (Piezoelectric)",
        "role": "Anti-tank / Anti-fortification",
        "usage": "Shoulder-launched rocket with a shaped charge for armor penetration."
    },
    "Rocket": {
        "weight": "5 - 100 kg",
        "origin": "USA, Russia, China, Iran",
        "ignition": "Impact / Remote Command",
        "role": "Tactical bombardment",
        "usage": "Self-propelled munition used for long-range surface-to-surface or air-to-surface strikes."
    },
    "Sea Mine": {
        "weight": "200 - 1000 kg",
        "origin": "UK, USA, Germany, Russia",
        "ignition": "Acoustic / Magnetic / Pressure",
        "role": "Naval area denial",
        "usage": "Underwater explosive device used to damage or destroy ships and submarines."
    },
    "AntiSubmarine Bomb": {
        "weight": "100 - 200 kg",
        "origin": "USA, Russia, UK, Japan",
        "ignition": "Hydrostatic (Depth sensing)",
        "role": "Anti-submarine warfare (ASW)",
        "usage": "Dropped from aircraft or ships to detonate at specific depths near submarines."
    },
    "Cartridge": {
        "weight": "0.01 - 0.2 kg",
        "origin": "Worldwide",
        "ignition": "Percussion Primer",
        "role": "Small arms ammunition",
        "usage": "Standard ammunition for rifles, pistols, and machine guns."
    },
    "Cartridge Magazine": {
        "weight": "0.2 - 0.5 kg",
        "origin": "Worldwide",
        "ignition": "N/A (Ammunition Holder)",
        "role": "Ammunition feeding system",
        "usage": "Container used to store and feed cartridges into a firearm."
    },
    "Fuse": {
        "weight": "0.1 - 0.5 kg",
        "origin": "Worldwide",
        "ignition": "Mechanical / Electrical / Chemical",
        "role": "Detonation trigger mechanism",
        "usage": "The device used to initiate the explosive train in larger ordnance."
    },
    "Unspecified UXO": {
        "weight": "Unknown (Varies widely)",
        "origin": "Unknown (Remnant of Conflict)",
        "ignition": "Deteriorated/Unstable",
        "role": "Unexploded Ordnance Hazard",
        "usage": "Abandoned or failed-to-detonate military explosive device.",
        "description": "General unexploded ordnance (UXO) detected from reference dataset. Handle with extreme caution as fuzing mechanisms may be highly unstable."
    }
}

def enrich_data():
    session = SessionLocal()
    try:
        # Get all seeded items (those that have empty tech fields)
        items = session.query(ExplosiveItem).filter(
            ExplosiveItem.country_of_origin == None
        ).all()
        
        print(f"Found {len(items)} items to enrich.")
        updated_count = 0
        
        for item in items:
            specs = TECH_SPECS_MAP.get(item.explosive_type)
            if specs:
                item.country_of_origin = specs["origin"]
                item.weight = specs["weight"]
                item.ignition_method = specs["ignition"]
                item.role = specs["role"]
                item.usage = specs["usage"]
                if "description" in specs:
                    item.description = specs["description"]
                updated_count += 1
                
        session.commit()
        print(f"Successfully enriched {updated_count} items with typical technical data.")
    except Exception as e:
        session.rollback()
        print(f"Error enriching data: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    enrich_data()
