import os
import sys
from sqlalchemy.orm import Session

# Add current directory to path
sys.path.append(os.getcwd())

from database import SessionLocal
from models import ExplosiveItem

def fix_urls():
    session = SessionLocal()
    try:
        items = session.query(ExplosiveItem).all()
        updated_count = 0
        for item in items:
            # Check if it's a local absolute path (starts with C: or contains project path)
            if item.image_url and ("extracted/images" in item.image_url) and not item.image_url.startswith("/"):
                filename = os.path.basename(item.image_url)
                item.image_url = f"/extracted/images/{filename}"
                updated_count += 1
        
        session.commit()
        print(f"Successfully updated {updated_count} image URLs.")
    except Exception as e:
        session.rollback()
        print(f"Error updating URLs: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    fix_urls()
