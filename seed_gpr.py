import os
import sys
import json
import uuid
import numpy as np
from PIL import Image
from sqlalchemy.orm import Session

# Add current directory to path
sys.path.append(os.getcwd())

from database import SessionLocal
from models import ExplosiveItem

def seed_gpr_data():
    filepath = r'C:\Users\ELITEBOOK X2\Desktop\HND EOT\PROJECT\polimi-ispl landmine_detection_autoencoder master datasets-giuriati_2\20170621_deg0_HHVV.npy'
    uploads_dir = os.path.join(os.getcwd(), "uploads")
    
    # Ensure uploads directory exists
    os.makedirs(uploads_dir, exist_ok=True)
    
    if not os.path.exists(filepath):
        print(f"Error: Dataset file not found at {filepath}")
        return
        
    print("Loading NumPy file...")
    try:
        raw_data = np.load(filepath, allow_pickle=True)
        if raw_data.ndim == 0:
            content = raw_data.item()
        else:
            print("Error: Expected a 0-dimensional dictionary array.")
            return
    except Exception as e:
        print(f"Error loading npy file: {e}")
        return
        
    data_array = content.get('data') # Shape (66, 170, 440)
    ground_truth = content.get('ground_truth') # Shape (66,)
    params = content.get('param', {})
    
    if data_array is None or ground_truth is None:
        print("Error: 'data' or 'ground_truth' not found in file content.")
        return
        
    num_samples = data_array.shape[0]
    print(f"Loaded GPR data. Number of samples: {num_samples}")
    
    session = SessionLocal()
    inserted = 0
    
    try:
        for i in range(num_samples):
            # Extract 2D slice
            slice_data = data_array[i] # Shape (170, 440)
            gt_val = int(ground_truth[i])
            
            # Normalize to 0-255 range
            min_val = slice_data.min()
            max_val = slice_data.max()
            if max_val > min_val:
                norm_data = (slice_data - min_val) / (max_val - min_val) * 255.0
            else:
                norm_data = np.zeros_like(slice_data)
            
            # Convert to PIL grayscale image
            img = Image.fromarray(norm_data.astype(np.uint8), mode='L')
            
            # Save image
            new_filename = f"gpr_{uuid.uuid4()}.png"
            dest_path = os.path.join(uploads_dir, new_filename)
            img.save(dest_path)
            
            # Map type and danger level based on GT
            # 1 = Landmine, 0 = Clutter (No mine)
            if gt_val == 1:
                item_type = "GPR Landmine Target"
                danger = 5
                description = f"GPR B-Scan sample {i} showing signature of a buried landmine."
            else:
                item_type = "GPR Clutter Target"
                danger = 1
                description = f"GPR B-Scan sample {i} showing clutter (false alarm/no landmine)."
                
            item = ExplosiveItem(
                name=f"GPR Scan Sample {i}",
                explosive_type=item_type,
                description=f"{description} Parameters: {str(params)}",
                danger_level=danger,
                image_url=f"/uploads/{new_filename}",
                metadata_signature={
                    "dataset": "polimi-ispl landmine_detection_autoencoder",
                    "sample_index": i,
                    "ground_truth": gt_val,
                    "parameters": params
                }
            )
            session.add(item)
            inserted += 1
            
        session.commit()
        print(f"Successfully seeded {inserted} GPR items into the database!")
    except Exception as e:
        session.rollback()
        print(f"Error during GPR seeding: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    seed_gpr_data()
