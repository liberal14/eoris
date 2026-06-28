import os
import sys
import json
import uuid
import shutil
from pathlib import Path
from sqlalchemy.orm import Session

# Add current directory to path
sys.path.append(os.getcwd())

from database import SessionLocal
from models import ExplosiveItem

def seed_v1i_data():
    dataset_dir = r"C:\Users\ELITEBOOK X2\Desktop\HND EOT\PROJECT\uxo.v1i.coco\train"
    json_path = os.path.join(dataset_dir, "_annotations.coco.json")
    uploads_dir = os.path.join(os.getcwd(), "uploads")
    
    # Ensure uploads directory exists
    os.makedirs(uploads_dir, exist_ok=True)
    
    with open(json_path, 'r') as f:
        coco_data = json.load(f)
        
    session = SessionLocal()
    inserted = 0
    
    # Map image_id to annotations
    ann_by_image = {}
    for ann in coco_data.get("annotations", []):
        img_id = ann.get("image_id")
        ann_by_image.setdefault(img_id, []).append(ann)
        
    print(f"Found {len(coco_data.get('images', []))} images in annotations.")
    
    try:
        for img in coco_data.get("images", []):
            file_name = img.get("file_name")
            image_id = img.get("id")
            source_path = os.path.join(dataset_dir, file_name)
            
            if not os.path.exists(source_path):
                print(f"Warning: Image {file_name} not found, skipping.")
                continue
                
            # Copy image to uploads
            file_ext = file_name.split(".")[-1]
            new_filename = f"{uuid.uuid4()}.{file_ext}"
            dest_path = os.path.join(uploads_dir, new_filename)
            shutil.copy2(source_path, dest_path)
            
            image_annotations = ann_by_image.get(image_id, [])
            
            item = ExplosiveItem(
                name=f"UXO Target ({Path(file_name).stem[:10]})",
                explosive_type="Unspecified UXO",
                description="Imported from uxo.v1i.coco dataset.",
                danger_level=4, # Default high for unknown UXOs
                metadata_signature={"image": img, "annotations": image_annotations},
                image_url=f"/uploads/{new_filename}"
            )
            session.add(item)
            inserted += 1
            
        session.commit()
        print(f"Successfully seeded {inserted} items into the database!")
    except Exception as e:
        session.rollback()
        print(f"Error during seeding: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    seed_v1i_data()
