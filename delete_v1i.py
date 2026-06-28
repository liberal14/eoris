import os
import sys
from sqlalchemy.orm import Session

# Add current directory to path
sys.path.append(os.getcwd())

from database import SessionLocal
from models import ExplosiveItem

def delete_v1i_data():
    session = SessionLocal()
    try:
        # Find all items that are Unspecified UXO
        items_to_delete = session.query(ExplosiveItem).filter(
            ExplosiveItem.explosive_type == "Unspecified UXO"
        ).all()
        
        print(f"Found {len(items_to_delete)} UXO items to delete.")
        
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
        print(f"Successfully deleted {len(items_to_delete)} database records and {deleted_files_count} associated image files.")
    except Exception as e:
        session.rollback()
        print(f"Error during deletion: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    delete_v1i_data()
