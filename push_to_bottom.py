import os
import sys
from datetime import datetime

# Add current directory to path
sys.path.append(os.getcwd())

from database import SessionLocal
from models import ExplosiveItem

def main():
    session = SessionLocal()
    
    # The image URLs of the items that were originally without proper names
    target_urls = [
        "/images/download.jpg",
        "/images/download (1).jpg",
        "/images/download (2).jpg",
        "/images/8WonafKZanpD29WACM3dCKC6jq9QBBc0JEyVcZyD.jpg",
        "/images/TD58AoDcPQKTk0mulPhhJbWEpTx55HxktBJoIYtj.jpg",
        "/images/ritgEPNjXScuZGx3IBZOHtE9isdZObCicz1uIh4M.jpg",
        "/images/sGgDmah0XygkNI0btMmkmlZh3ysAPWq3G5bqVpj0.jpg"
    ]
    
    # Set their created_at date to something very old so they sort to the bottom
    old_date = datetime(2000, 1, 1)
    
    count = 0
    for url in target_urls:
        item = session.query(ExplosiveItem).filter(ExplosiveItem.image_url == url).first()
        if item:
            item.created_at = old_date
            count += 1
            print(f"Pushed to bottom: {item.name}")
            
    session.commit()
    print(f"Successfully pushed {count} items to the bottom of the page.")
    session.close()

if __name__ == "__main__":
    main()
