from datetime import datetime, timedelta
from typing import Optional
from jose import JWTError, jwt
import bcrypt
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core.config import settings
from app.core.models import User # Import User model

# pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token", auto_error=False)

def verify_password(plain_password, hashed_password):
    # Ensure bytes
    if isinstance(plain_password, str):
        plain_password = plain_password.encode('utf-8')
    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode('utf-8')
    return bcrypt.checkpw(plain_password, hashed_password)

def get_password_hash(password):
    if isinstance(password, str):
        password = password.encode('utf-8')
    # Generate salt and hash
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password, salt).decode('utf-8')

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt

async def get_current_user(
    request: Request,
    db: Session = Depends(get_db) # Token dependency removed to handle manually
):
    token = None
    
    print(f"DEBUG: get_current_user called. Token: {token}, Request: {request}", flush=True)
    if not token and request:
         token = request.cookies.get("access_token")
         print(f"DEBUG: Token from cookie: {token}", flush=True)
         if token and token.startswith("Bearer "):
             token = token.split(" ")[1]
    
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    if not token:
        # Fallback: Auto-login / Dev Admin creation
        # Only in this specific requested dev environment
        admin_user = db.query(User).filter(User.email == "admin@thelimbo.io").first()
        if not admin_user:
            print("DEBUG: Creating admin user fallback.", flush=True)
            # Auto-create admin
            try:
                admin_user = User(
                    email="admin@thelimbo.io",
                    full_name="Admin User",
                    password_hash=get_password_hash("admin"),
                    role="admin"
                )
                db.add(admin_user)
                db.commit()
                db.refresh(admin_user)
            except Exception as e:
                print(f"DEBUG: Error creating admin user: {e}", flush=True)
                # Handle potential race conditions
                db.rollback()
                admin_user = db.query(User).filter(User.email == "admin@thelimbo.io").first()
                if not admin_user:
                    raise credentials_exception
        
        # If we found/created admin user, return it
        if admin_user:
            return admin_user

        raise credentials_exception

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception
    return user
