import os
import sys
import json
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

# Add current directory to path
sys.path.append(os.getcwd())

from database import SessionLocal
from models import ExplosiveItem

def seed_detailed_bombs():
    session = SessionLocal()
    
    try:
        # Load the dataset
        file_path = os.path.join(os.getcwd(), 'bombs_dataset.json')
        with open(file_path, 'r') as f:
            bombs_data = json.load(f)
            
        print(f"Loaded {len(bombs_data)} bombs from dataset.")
        
        inserted_count = 0
        for bomb in bombs_data:
            # Check if bomb already exists
            existing = session.query(ExplosiveItem).filter(
                ExplosiveItem.name == bomb["name"]
            ).first()
            
            if existing:
                print(f"Bomb '{bomb['name']}' already exists. Skipping.")
                continue
                
            # Create new ExplosiveItem
            new_item = ExplosiveItem(
                name=bomb["name"],
                explosive_type=bomb["explosive_type"],
                danger_level=bomb["danger_level"],
                description=bomb["description"],
                country_of_origin=bomb["country_of_origin"],
                weight=bomb["weight"],
                ignition_method=bomb["ignition_method"],
                role=bomb["role"],
                usage=bomb["usage"],
                # Store the highly detailed dictionary in the JSON column
                metadata_signature=bomb["metadata_signature"]
            )
            
            session.add(new_item)
            inserted_count += 1
            
        session.commit()
        print(f"Successfully inserted {inserted_count} new detailed bombs into the database.")
        
    except FileNotFoundError:
        print("Error: bombs_dataset.json not found.")
    except SQLAlchemyError as e:
        session.rollback()
        print(f"Database error: {e}")
    except Exception as e:
        session.rollback()
        print(f"An unexpected error occurred: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    seed_detailed_bombs()
