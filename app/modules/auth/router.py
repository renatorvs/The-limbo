from fastapi import APIRouter, Depends, HTTPException, Response, Request, status
from fastapi.templating import Jinja2Templates
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.core import security
from app.core.models import User
from app.modules.auth import schemas
from uuid import UUID

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

# --- HTML Views ---
@router.get("/login", include_in_schema=False)
def login_page(request: Request):
    return templates.TemplateResponse("auth/login.html", {"request": request})

@router.get("/register", include_in_schema=False)
def register_page(request: Request):
    return templates.TemplateResponse("auth/register.html", {"request": request})

@router.get("/logout", include_in_schema=False)
def logout(response: Response):
    response = RedirectResponse(url="/api/v1/auth/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("access_token")
    return response

# --- API Endpoints ---
@router.post("/register", response_model=schemas.Token)
def register(user_data: schemas.UserCreate, response: Response, db: Session = Depends(get_db)):
    # Check if user exists
    user = db.query(User).filter(User.email == user_data.email).first()
    if user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    # Create user
    new_user = User(
        email=user_data.email,
        full_name=user_data.full_name or user_data.email.split("@")[0],
        password_hash=security.get_password_hash(user_data.password),
        role="user" # Default role
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    # Auto-login
    access_token = security.create_access_token(data={"sub": new_user.email})
    response.set_cookie(
        key="access_token", 
        value=f"Bearer {access_token}", 
        httponly=True,
        max_age=18000
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/login", response_model=schemas.Token)
def login(login_data: schemas.UserLogin, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == login_data.email).first()
    if not user or not security.verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = security.create_access_token(data={"sub": user.email})
    response.set_cookie(
        key="access_token", 
        value=f"Bearer {access_token}", 
        httponly=True,
        max_age=18000 # 5 hours
    )
    return {"access_token": access_token, "token_type": "bearer"}

@router.post("/switch-context/{company_id}")
def switch_company_context(
    company_id: UUID, 
    response: Response,
    db: Session = Depends(get_db),
    current_user: User = Depends(security.get_current_user)
):
    # 1. Update User's current company in DB (persistence)
    current_user.company_id = company_id
    db.commit()
    
    return {"message": "Context switched", "company_id": str(company_id)}

@router.post("/dev-login")
def dev_login(response: Response, db: Session = Depends(get_db)):
    # Auto-login as admin for dev
    user = db.query(User).filter(User.email == "admin@thelimbo.io").first()
    if not user:
        # Create dev admin if not exists
        user = User(
            email="admin@thelimbo.io",
            full_name="Admin User",
            password_hash=security.get_password_hash("admin"),
            role="admin"
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    access_token = security.create_access_token(data={"sub": user.email})
    response.set_cookie(
        key="access_token", 
        value=f"Bearer {access_token}", 
        httponly=True,
        max_age=18000
    )
    return {"message": "Logged in as Admin", "access_token": access_token}
