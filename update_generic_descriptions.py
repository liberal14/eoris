import os
import sys

# Add current directory to path
sys.path.append(os.getcwd())

from database import SessionLocal
from models import ExplosiveItem

def get_description_mapping():
    return {
        "120 Amraam": "AIM-120 Advanced Medium-Range Air-to-Air Missile (AMRAAM). An American beyond-visual-range air-to-air missile capable of all-weather day-and-night operations.",
        "120Mm Rocket": "120mm unguided or guided air-to-ground/artillery rocket.",
        "20Lbmk1 002": "20 lb Mk 1 fragmentation bomb, an early air-dropped anti-personnel bomb.",
        "250 Kg Fab Bomb": "FAB-250, a Soviet-designed 250 kg general-purpose air-dropped bomb.",
        "250 Kg M53B Bomb": "M53B 250kg bomb, a general-purpose explosive weapon.",
        "250 Kg Ofab Bomb": "OFAB-250, a Soviet-designed 250 kg high-explosive fragmentation bomb.",
        "250Kg R Baker Bomb": "250kg general purpose bomb.",
        "250Kg Bomb": "250kg general purpose bomb used for strike missions against unarmored targets.",
        "250Kg General Purpose Low Drag Bomb South Africa": "South African designed 250kg low-drag general purpose aerial bomb.",
        "250Kg General Purpose Low Drag Bomb": "250kg low-drag general purpose bomb designed for high-speed delivery.",
        "3Kg 001": "3kg small air-dropped submunition or anti-personnel bomb.",
        "4000Lbgp 001": "4000 lb general purpose aerial bomb (often referred to as a 'Cookie' or block-buster bomb).",
        "57Mm Rocket": "57mm unguided rocket, such as the Soviet S-5 series, used heavily in air-to-ground strikes.",
        "80Mm S8 Rocket": "S-8 80mm unguided air-to-ground rocket developed by the Soviet Union for use by attack aircraft and helicopters.",
        "Hydra 70Mm Rocket": "Hydra 70, a widely used 70mm (2.75 inch) fin-stabilized unguided rocket.",
        "Mk 82 Bomb": "Mark 82, a 500-pound unguided, low-drag general-purpose bomb part of the US Mk 80 series.",
        "Ofab 250 270 Bomb": "OFAB-250-270, a Soviet-designed 250 kg high-explosive fragmentation air-dropped bomb.",
        "Sneb 68 Type 23 Rocket": "SNEB 68mm unguided air-to-ground rocket projectile, widely used in French and other Western aircraft.",
        "Sneb 68 Type 26 Rocket": "SNEB 68mm unguided air-to-ground rocket projectile, widely used in French and other Western aircraft.",
        "Type 90 1 Rocket": "Type 90 122mm unguided rocket or 90mm air-to-ground rocket.",
        "A N M41 001": "AN-M41 20-pound fragmentation bomb used by the US military.",
        "Agm 62 001": "AGM-62 Walleye, a United States television-guided glide bomb.",
        "An M88 001": "AN-M88 216-pound fragmentation bomb.",
        "Bafg 120 001": "BAFG-120 general purpose aerial bomb.",
        "Be 500 001": "BE 500 series aerial bomb.",
        "Belouga 66 Bomb": "BLG 66 Belouga, a French air-dropped cluster bomb dispensing anti-armour or anti-personnel submunitions.",
        "Durandal Anti Runway Bomb": "BLU-107/B Durandal, a French-designed penetration bomb specifically developed to crater and destroy airport runways.",
        "Durandal Cluster Bomb": "A variant or submunition package based on the Durandal system for runway denial."
    }

def main():
    session = SessionLocal()
    mapping = get_description_mapping()
    
    # Update all items with generic descriptions
    items = session.query(ExplosiveItem).filter(ExplosiveItem.description.like('%Imported from the local image library%')).all()
    count = 0
    for item in items:
        # Give it a proper description based on mapping, or at least a clean generic one if not found
        new_desc = mapping.get(item.name)
        if not new_desc:
            new_desc = f"{item.name} is a military explosive ordnance or aerial bomb."
            
        item.description = new_desc
        count += 1
        print(f"Updated description for: {item.name}")

    session.commit()
    print(f"\nSuccessfully updated {count} items.")
    session.close()

if __name__ == "__main__":
    main()
