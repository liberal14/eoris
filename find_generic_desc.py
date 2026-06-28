import os
import sys

# Add current directory to path
sys.path.append(os.getcwd())

from database import SessionLocal
from models import ExplosiveItem

def main():
    session = SessionLocal()
    
    items = session.query(ExplosiveItem).filter(ExplosiveItem.description.like('%Imported from the local image library%')).all()
    
    for item in items:
        print(f"ID: {item.id} | Name: {item.name}")

    session.close()

if __name__ == "__main__":
    main()
