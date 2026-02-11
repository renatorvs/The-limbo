from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.database import get_db
from . import schemas, service

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/dashboard")
def view_dashboard(request: Request, db: Session = Depends(get_db)):
    bank_accounts = service.get_bank_accounts(db)
    cost_centers = service.get_cost_centers(db)
    stats = service.get_financial_stats(db)
    ledger_entries = service.get_recent_transactions(db)
    
    return templates.TemplateResponse("dashboard/backbone.html", {
        "request": request, 
        "bank_accounts": bank_accounts,
        "cost_centers": cost_centers,
        "stats": stats,
        "ledger_entries": ledger_entries
    })

@router.get("/companies_view")
def view_companies(request: Request, db: Session = Depends(get_db)):
    companies = service.get_companies(db, limit=100)
    return templates.TemplateResponse("dashboard/companies.html", {"request": request, "companies": companies})

@router.post("/companies", response_model=schemas.CompanyOut)
def create_company(company: schemas.CompanyCreate, db: Session = Depends(get_db)):
    return service.create_company(db=db, company=company)

@router.get("/companies", response_model=list[schemas.CompanyOut])
def get_companies(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return service.get_companies(db, skip, limit)

@router.post("/bank-accounts", response_model=schemas.BankAccountOut)
def create_bank_account(bank_account: schemas.BankAccountCreate, db: Session = Depends(get_db)):
    return service.create_bank_account(db, bank_account)

@router.get("/bank-accounts", response_model=list[schemas.BankAccountOut])
def get_bank_accounts(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return service.get_bank_accounts(db, skip, limit)

@router.post("/transaction", response_model=schemas.LedgerOut)
def create_transaction(transaction: schemas.LedgerCreate, db: Session = Depends(get_db)):
    return service.create_transaction(db=db, transaction=transaction)

@router.get("/transactions", response_model=list[schemas.LedgerOut])
def get_transactions(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return service.get_transactions(db, skip, limit)

@router.get("/runway")
def get_runway_stats(db: Session = Depends(get_db)):
    return service.get_runway(db=db)

# Cost Centers
@router.post("/costcenter", response_model=schemas.CostCenterOut)
def create_cost_center(costcenter: schemas.CostCenterCreate, db: Session = Depends(get_db)):
    return service.create_cost_center(db, costcenter)

@router.get("/costcenter", response_model=list[schemas.CostCenterOut])
def get_cost_centers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return service.get_cost_centers(db, skip, limit)

# Staff
@router.post("/staff", response_model=schemas.StaffOut)
def create_staff(staff: schemas.StaffCreate, db: Session = Depends(get_db)):
    return service.create_staff(db, staff)

@router.get("/staff", response_model=list[schemas.StaffOut])
def get_staff(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return service.get_staff(db, skip, limit)
