from sqlalchemy.orm import Session
from sqlalchemy import func
from . import models, schemas
from app.core.models import Company
from datetime import datetime
from uuid import UUID
from typing import Optional

def _co_filter(query, model, company_id: Optional[UUID]):
    if company_id is not None:
        return query.filter(model.company_id == company_id)
    return query

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

def get_bank_accounts(db: Session, skip: int = 0, limit: int = 100, company_id: Optional[UUID] = None):
    q = _co_filter(db.query(models.BankAccount), models.BankAccount, company_id)
    return q.offset(skip).limit(limit).all()

def create_transaction(db: Session, transaction: schemas.LedgerCreate):
    db_txn = models.Ledger(**transaction.dict())
    db.add(db_txn)
    db.commit()
    db.refresh(db_txn)
    return db_txn

def get_transactions(db: Session, skip: int = 0, limit: int = 100, company_id: Optional[UUID] = None):
    q = _co_filter(db.query(models.Ledger), models.Ledger, company_id)
    return q.offset(skip).limit(limit).all()

def get_runway(db: Session, company_id: Optional[UUID] = None):
    stats = get_financial_stats(db, company_id)
    months = round(stats.total_balance / stats.burn_rate, 1) if stats.burn_rate > 0 else None
    return {"months_left": months, "burn_rate": stats.burn_rate}

def create_cost_center(db: Session, costcenter: schemas.CostCenterCreate):
    db_obj = models.CostCenter(**costcenter.dict())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def get_cost_centers(db: Session, skip: int = 0, limit: int = 100, company_id: Optional[UUID] = None):
    q = _co_filter(db.query(models.CostCenter), models.CostCenter, company_id)
    return q.offset(skip).limit(limit).all()

def create_staff(db: Session, staff: schemas.StaffCreate):
    db_obj = models.Staff(**staff.dict())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def get_staff(db: Session, skip: int = 0, limit: int = 100, company_id: Optional[UUID] = None):
    q = _co_filter(db.query(models.Staff), models.Staff, company_id)
    return q.offset(skip).limit(limit).all()

def get_financial_stats(db: Session, company_id: Optional[UUID] = None):
    q_bal = db.query(func.sum(models.BankAccount.current_balance))
    if company_id:
        q_bal = q_bal.filter(models.BankAccount.company_id == company_id)
    total_balance = q_bal.scalar() or 0.0

    q_burn = db.query(func.sum(models.Ledger.amount)).filter(models.Ledger.type == 'opex')
    if company_id:
        q_burn = q_burn.filter(models.Ledger.company_id == company_id)
    burn_rate = q_burn.scalar() or 0.0

    q_hc = db.query(func.count(models.Staff.id)).filter(models.Staff.terminated_at == None)
    if company_id:
        q_hc = q_hc.filter(models.Staff.company_id == company_id)
    headcount = q_hc.scalar() or 0

    return schemas.FinancialStats(
        total_balance=float(total_balance),
        burn_rate=float(burn_rate),
        headcount=int(headcount)
    )

def get_recent_transactions(db: Session, limit: int = 10, company_id: Optional[UUID] = None):
    q = db.query(models.Ledger)
    if company_id:
        q = q.filter(models.Ledger.company_id == company_id)
    return q.order_by(models.Ledger.transaction_date.desc()).limit(limit).all()
