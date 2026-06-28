import os
import sys
from pathlib import Path
from sqlalchemy import or_

sys.path.append(os.getcwd())

from database import SessionLocal
from models import ExplosiveItem

def delete_gpr_data():
    session = SessionLocal()
    try:
        # Find all items that are GPR targets or have "gpr_" in their image URL
        items_to_delete = session.query(ExplosiveItem).filter(
            or_(
                ExplosiveItem.explosive_type == "GPR Landmine Target",
                ExplosiveItem.explosive_type == "GPR Clutter Target",
                ExplosiveItem.image_url.like("%gpr_%")
            )
        ).all()
        
        print(f"Found {len(items_to_delete)} GPR items to delete.")
        
        deleted_files_count = 0
        for item in items_to_delete:
            # Delete image file if it exists
            if item.image_url:
                # Remove leading slash if present
                relative_path = item.image_url.lstrip('/')
                file_path = os.path.join(os.getcwd(), relative_path)
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        deleted_files_count += 1
                    except Exception as e:
                        print(f"Error deleting file {file_path}: {e}")
            
            # Delete DB record
            session.delete(item)
            
        session.commit()
        print(f"Successfully deleted {len(items_to_delete)} GPR database records and {deleted_files_count} associated image files.")
    except Exception as e:
        session.rollback()
        print(f"Error during deletion: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    delete_gpr_data()
