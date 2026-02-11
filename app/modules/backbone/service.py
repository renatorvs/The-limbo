from sqlalchemy.orm import Session
from sqlalchemy import func
from . import models, schemas
from app.core.models import Company
from datetime import datetime

def create_company(db: Session, company: schemas.CompanyCreate):
    db_company = Company(**company.dict())
    db.add(db_company)
    db.commit()
    db.refresh(db_company)
    return db_company

def get_companies(db: Session, skip: int = 0, limit: int = 100):
    return db.query(Company).offset(skip).limit(limit).all()

def create_bank_account(db: Session, bank_account: schemas.BankAccountCreate):
    db_obj = models.BankAccount(**bank_account.dict())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def get_bank_accounts(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.BankAccount).offset(skip).limit(limit).all()

def create_transaction(db: Session, transaction: schemas.LedgerCreate):
    db_txn = models.Ledger(**transaction.dict())
    db.add(db_txn)
    db.commit()
    db.refresh(db_txn)
    return db_txn

def get_transactions(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Ledger).offset(skip).limit(limit).all()

def get_runway(db: Session):
    # Mock logic for runway calculation
    return {"months_left": 12, "burn_rate": 50000.0}

def create_cost_center(db: Session, costcenter: schemas.CostCenterCreate):
    db_obj = models.CostCenter(**costcenter.dict())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def get_cost_centers(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.CostCenter).offset(skip).limit(limit).all()

def create_staff(db: Session, staff: schemas.StaffCreate):
    db_obj = models.Staff(**staff.dict())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def get_staff(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Staff).offset(skip).limit(limit).all()

def get_financial_stats(db: Session):
    # Total Balance
    total_balance = db.query(func.sum(models.BankAccount.current_balance)).scalar() or 0.0

    # Burn Rate (Simple: Sum of OPEX transactions) - Ideally filter by date
    burn_rate = db.query(func.sum(models.Ledger.amount)).filter(models.Ledger.type == 'opex').scalar() or 0.0

    # Headcount (Active staff)
    headcount = db.query(func.count(models.Staff.id)).filter(models.Staff.terminated_at == None).scalar() or 0

    return schemas.FinancialStats(
        total_balance=float(total_balance),
        burn_rate=float(burn_rate),
        headcount=int(headcount)
    )

def get_recent_transactions(db: Session, limit: int = 10):
    return db.query(models.Ledger).order_by(models.Ledger.transaction_date.desc()).limit(limit).all()
