import os
import uuid
from typing import List, Optional
from datetime import datetime, timedelta
from fastapi import FastAPI, Depends, Request, Form, File, UploadFile, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
import shutil
import jwt
import bcrypt
import re
import random
import string
import smtplib
from email.mime.text import MIMEText

def send_otp_email(to_email: str, otp: str):
    smtp_server = os.getenv("SMTP_SERVER")
    smtp_port = os.getenv("SMTP_PORT")
    smtp_user = os.getenv("SMTP_USERNAME")
    smtp_pass = os.getenv("SMTP_PASSWORD")
    
    if not all([smtp_server, smtp_port, smtp_user, smtp_pass]):
        print(f"==========================================")
        print(f"SMTP not configured.")
        print(f"OTP for {to_email} is: {otp}")
        print(f"==========================================")
        return
    
    try:
        msg = MIMEText(f"Your EORIS verification code is: {otp}")
        msg['Subject'] = 'EORIS Account Verification'
        msg['From'] = smtp_user
        msg['To'] = to_email
        
        server = smtplib.SMTP(smtp_server, int(smtp_port))
        server.starttls()
        server.login(smtp_user, smtp_pass)
        server.send_message(msg)
        server.quit()
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")
        print(f"Fallback OTP for {to_email} is: {otp}")

from database import get_db, engine
from models import ExplosiveItem, User, Base
from image_logic import get_image_metadata, get_image_phash, get_feature_vector, cosine_similarity

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(title="EORIS (Explosive Ordnance Recognition & Identification System)")

# Auth settings
SECRET_KEY = "your-super-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24

def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False

def get_password_hash(password: str) -> str:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user_optional(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get("access_token")
    if not token:
        return None
    try:
        # FastAPI might prefix with 'Bearer '
        if token.startswith("Bearer "):
            token = token.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            return None
    except jwt.PyJWTError:
        return None
    user = db.query(User).filter(User.username == username).first()
    return user

async def get_current_user_required(request: Request, db: Session = Depends(get_db)):
    user = await get_current_user_optional(request, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/uploads", StaticFiles(directory="uploads"), name="uploads")
app.mount("/extracted", StaticFiles(directory="extracted"), name="extracted")

# Mount the extra images folder if it exists
if os.path.isdir("images"):
    app.mount("/images", StaticFiles(directory="images"), name="images")

templates = Jinja2Templates(directory="templates")

# Ensure upload directory exists
os.makedirs("uploads", exist_ok=True)
os.makedirs("images", exist_ok=True)

# Authentication routes
@app.get("/register", response_class=HTMLResponse)
async def read_register(request: Request, user: Optional[User] = Depends(get_current_user_optional)):
    return templates.TemplateResponse(request=request, name="register.html", context={"user": user})

@app.post("/register")
async def register(request: Request, username: str = Form(...), email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.username == username).first()
    if db_user:
        return templates.TemplateResponse(request=request, name="register.html", context={"error": "Username already registered", "user": None})
    
    db_email = db.query(User).filter(User.email == email).first()
    if db_email:
        return templates.TemplateResponse(request=request, name="register.html", context={"error": "Email already exists", "user": None})
    
    if not re.search(r'[A-Z]', password) or not re.search(r'[a-z]', password) or not re.search(r'[^a-zA-Z0-9]', password):
        return templates.TemplateResponse(request=request, name="register.html", context={"error": "Password must contain at least one uppercase letter, one lowercase letter, and one special character.", "user": None})
    
    hashed_password = get_password_hash(password)
    otp_code = ''.join(random.choices(string.digits, k=6))
    expire_time = datetime.utcnow() + timedelta(minutes=10)
    
    db_user = User(username=username, email=email, hashed_password=hashed_password, is_verified=False, otp=otp_code, otp_expires_at=expire_time)
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    send_otp_email(email, otp_code)
    return RedirectResponse(url=f"/verify-otp?username={username}", status_code=303)

@app.get("/login", response_class=HTMLResponse)
async def read_login(request: Request, user: Optional[User] = Depends(get_current_user_optional)):
    return templates.TemplateResponse(request=request, name="login.html", context={"user": user})

@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        total_records = db.query(ExplosiveItem).count()
        total_countries = db.query(ExplosiveItem.country_of_origin).filter(ExplosiveItem.country_of_origin != None).distinct().count()
        total_categories = db.query(ExplosiveItem.explosive_type).filter(ExplosiveItem.explosive_type != None).distinct().count()
        return templates.TemplateResponse(
            request=request, 
            name="index.html", 
            context={
                "error": "Incorrect username or password", 
                "user": None,
                "total_records": total_records,
                "total_countries": total_countries,
                "total_categories": total_categories
            }
        )
    
    if not getattr(user, 'is_verified', True):
        return RedirectResponse(url=f"/verify-otp?username={username}", status_code=303)
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return response

@app.get("/verify-otp", response_class=HTMLResponse)
async def read_verify_otp(request: Request, username: str = ""):
    return templates.TemplateResponse(request=request, name="verify_otp.html", context={"username": username, "user": None})

@app.post("/verify-otp")
async def verify_otp(request: Request, username: str = Form(...), otp: str = Form(...), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == username).first()
    if not user:
        return templates.TemplateResponse(request=request, name="verify_otp.html", context={"error": "User not found", "username": username, "user": None})
    
    if getattr(user, 'is_verified', False):
        return RedirectResponse(url="/login", status_code=303)
        
    if user.otp != otp:
        return templates.TemplateResponse(request=request, name="verify_otp.html", context={"error": "Invalid OTP", "username": username, "user": None})
        
    if user.otp_expires_at and datetime.utcnow() > user.otp_expires_at:
        return templates.TemplateResponse(request=request, name="verify_otp.html", context={"error": "OTP has expired. Please request a new one by re-registering.", "username": username, "user": None})
        
    user.is_verified = True
    user.otp = None
    user.otp_expires_at = None
    db.commit()
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    response = RedirectResponse(url="/", status_code=303)
    response.set_cookie(key="access_token", value=f"Bearer {access_token}", httponly=True)
    return response

@app.get("/logout")
async def logout():
    response = RedirectResponse(url="/", status_code=303)
    response.delete_cookie("access_token")
    return response

# Main App Routes
@app.get("/", response_class=HTMLResponse)
async def read_dashboard(request: Request, db: Session = Depends(get_db), user: Optional[User] = Depends(get_current_user_optional)):
    total_records = db.query(ExplosiveItem).count()
    total_countries = db.query(ExplosiveItem.country_of_origin).filter(ExplosiveItem.country_of_origin != None).distinct().count()
    total_categories = db.query(ExplosiveItem.explosive_type).filter(ExplosiveItem.explosive_type != None).distinct().count()

    if user:
        # Authenticated users see all explosives on the dashboard
        items = db.query(ExplosiveItem).order_by(ExplosiveItem.created_at.desc()).all()
        return templates.TemplateResponse(
            request=request,
            name="dashboard.html",
            context={
                "items": items,
                "user": user,
                "total_records": total_records,
                "total_countries": total_countries,
                "total_categories": total_categories
            }
        )
    else:
        # Unauthenticated users see the landing page
        return templates.TemplateResponse(
            request=request,
            name="index.html",
            context={
                "user": user,
                "total_records": total_records,
                "total_countries": total_countries,
                "total_categories": total_categories
            }
        )

@app.get("/scanner", response_class=HTMLResponse)
async def read_scanner(request: Request, user: Optional[User] = Depends(get_current_user_optional)):
    if not user:
        return RedirectResponse(url="/login", status_code=303)
    return templates.TemplateResponse(
    request=request,
    name="scanner.html",
    context={"user": user}
)

@app.post("/explosives/add")
async def add_explosive(
    name: str = Form(...),
    explosive_type: str = Form(...),
    description: str = Form(...),
    danger_level: int = Form(...),
    country_of_origin: str = Form(None),
    weight: str = Form(None),
    usage: str = Form(None),
    ignition_method: str = Form(None),
    role: str = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user_required)
):
    # Save file
    file_ext = file.filename.split(".")[-1]
    filename = f"{uuid.uuid4()}.{file_ext}"
    file_path = os.path.join("uploads", filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Process image – extract both pHash (fallback) and deep feature vector (primary)
    metadata = get_image_metadata(file_path)
    phash = get_image_phash(file_path)
    fvec  = get_feature_vector(file_path)   # 512-dim ResNet18 embedding
    
    new_item = ExplosiveItem(
        name=name,
        explosive_type=explosive_type,
        description=description,
        danger_level=danger_level,
        country_of_origin=country_of_origin,
        weight=weight,
        usage=usage,
        ignition_method=ignition_method,
        role=role,
        metadata_signature=metadata,
        image_hash=phash,
        feature_vector=fvec,
        image_url=f"/uploads/{filename}"
    )
    
    db.add(new_item)
    db.commit()
    db.refresh(new_item)
    
    return RedirectResponse(url="/", status_code=303)

@app.post("/identify")
async def identify_image(file: UploadFile = File(...), db: Session = Depends(get_db), user: Optional[User] = Depends(get_current_user_optional)):
    # Save temporary file for processing
    temp_filename = f"temp_{uuid.uuid4()}.jpg"
    temp_path = os.path.join("uploads", temp_filename)
    
    with open(temp_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # ── Step 1: extract features from the uploaded image ──────────────────────
    try:
        upload_metadata = get_image_metadata(temp_path)
        upload_phash    = get_image_phash(temp_path)
        upload_vector   = get_feature_vector(temp_path)   # 512-dim ResNet18 embedding
    except Exception as e:
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=f"Feature extraction failed: {str(e)}")

    all_items  = db.query(ExplosiveItem).all()
    scored_items = []

    # ── Step 2: Compute similarity for all items ──────────────────────────────
    import imagehash
    for item in all_items:
        score = 0.0
        # Primary: Deep feature vector matching
        if upload_vector and item.feature_vector:
            score = cosine_similarity(upload_vector, item.feature_vector)
        # Fallback: Perceptual hash matching
        elif upload_phash and item.image_hash:
            try:
                uploaded_h = imagehash.hex_to_hash(upload_phash)
                item_h     = imagehash.hex_to_hash(item.image_hash)
                distance   = uploaded_h - item_h
                # Map distance (0 to 64) to a 0.0 to 1.0 similarity metric
                score = max(0.0, 1.0 - (distance / 64.0))
            except Exception:
                score = 0.0
        
        if score > 0.0:
            scored_items.append((item, score))

    # Sort descending by score
    scored_items.sort(key=lambda x: x[1], reverse=True)

    # Clean up temp file
    if os.path.exists(temp_path):
        try:
            os.remove(temp_path)
        except Exception:
            pass

    HIGH_CONFIDENCE_THRESHOLD = 0.85
    LOW_CONFIDENCE_THRESHOLD  = 0.55

    # Determine status
    if not scored_items or scored_items[0][1] < LOW_CONFIDENCE_THRESHOLD:
        return {
            "status": "not_found",
            "upload_metadata": upload_metadata,
            "suggestions": []
        }

    top_item, top_score = scored_items[0]
    
    # Select top 3 suggestions (score >= LOW_CONFIDENCE_THRESHOLD)
    suggestions_list = []
    for item, score in scored_items[:3]:
        if score >= LOW_CONFIDENCE_THRESHOLD:
            suggestions_list.append({
                "id": item.id,
                "name": item.name,
                "type": item.explosive_type,
                "description": item.description,
                "danger_level": item.danger_level,
                "image_url": item.image_url,
                "country_of_origin": item.country_of_origin,
                "weight": item.weight,
                "usage": item.usage,
                "ignition_method": item.ignition_method,
                "role": item.role,
                "confidence": round(score * 100, 1)
            })

    if top_score >= HIGH_CONFIDENCE_THRESHOLD:
        return {
            "status": "success",
            "upload_metadata": upload_metadata,
            "match": {
                "id": top_item.id,
                "name": top_item.name,
                "type": top_item.explosive_type,
                "description": top_item.description,
                "danger_level": top_item.danger_level,
                "image_url": top_item.image_url,
                "country_of_origin": top_item.country_of_origin,
                "weight": top_item.weight,
                "usage": top_item.usage,
                "ignition_method": top_item.ignition_method,
                "role": top_item.role,
                "confidence": round(top_score * 100, 1)
            },
            "suggestions": suggestions_list
        }
    else:
        return {
            "status": "uncertain",
            "upload_metadata": upload_metadata,
            "suggestions": suggestions_list
        }

@app.get("/search")
async def search_by_name(q: str = "", db: Session = Depends(get_db)):
    """Search explosives by name (case-insensitive partial match)."""
    if not q or len(q.strip()) < 2:
        return {"results": []}

    query = q.strip()
    matches = db.query(ExplosiveItem).filter(
        ExplosiveItem.name.ilike(f"%{query}%")
    ).order_by(ExplosiveItem.name).limit(10).all()

    results = []
    for item in matches:
        results.append({
            "id": item.id,
            "name": item.name,
            "explosive_type": item.explosive_type,
            "description": item.description,
            "danger_level": item.danger_level,
            "image_url": item.image_url,
            "country_of_origin": item.country_of_origin,
            "weight": item.weight,
            "usage": item.usage,
            "ignition_method": item.ignition_method,
            "role": item.role,
        })

    return {"results": results}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
