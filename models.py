from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, Boolean
from datetime import datetime
from database import Base

class ExplosiveItem(Base):
    __tablename__ = "explosives"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    explosive_type = Column(String(100)) # 'bomb', 'mine', etc.
    description = Column(Text)
    danger_level = Column(Integer) # 1-5
    metadata_signature = Column(JSON) # JSON of relevant EXIF tags
    image_hash = Column(String(64), index=True) # Perceptual hash for visual search (fallback)
    feature_vector = Column(JSON, nullable=True)  # 512-dim ResNet18 embedding for semantic matching
    image_url = Column(String(512))
    country_of_origin = Column(String(100))
    weight = Column(String(50))
    usage = Column(Text)
    ignition_method = Column(String(255))
    role = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    is_verified = Column(Boolean, default=False)
    otp = Column(String(6), nullable=True)
    otp_expires_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
