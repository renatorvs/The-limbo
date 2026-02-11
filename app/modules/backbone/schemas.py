from pydantic import BaseModel
from datetime import date, datetime
from typing import Optional
from uuid import UUID

# Company
class CompanyBase(BaseModel):
    name: str
    cnpj_or_tax_id: Optional[str] = None
    industry: Optional[str] = None
    logo_url: Optional[str] = None

class CompanyCreate(CompanyBase):
    pass

class CompanyOut(CompanyBase):
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        orm_mode = True

# Bank Account
class BankAccountBase(BaseModel):
    bank_name: str
    account_type: str
    current_balance: float
    currency: str

class BankAccountCreate(BankAccountBase):
    company_id: Optional[UUID] = None

class BankAccountOut(BankAccountBase):
    id: UUID
    company_id: Optional[UUID] = None

    class Config:
        orm_mode = True

# Cost Center
class CostCenterBase(BaseModel):
    name: str
    code: str
    budget_limit: float

class CostCenterCreate(CostCenterBase):
    company_id: Optional[UUID] = None

class CostCenterOut(CostCenterBase):
    id: UUID
    company_id: Optional[UUID] = None
    created_at: datetime

    class Config:
        orm_mode = True

# Ledger
class LedgerBase(BaseModel):
    transaction_date: date
    description: str
    amount: float
    type: str
    is_recurring: bool = False
    recurrence_period: Optional[str] = None
    status: str
    document_url: Optional[str] = None
    external_transaction_id: Optional[str] = None
    cost_center_id: Optional[UUID] = None
    account_id: Optional[UUID] = None

class LedgerCreate(LedgerBase):
    company_id: Optional[UUID] = None

class LedgerOut(LedgerBase):
    id: UUID
    company_id: Optional[UUID] = None
    created_at: datetime

    class Config:
        orm_mode = True

# Staff
class StaffBase(BaseModel):
    full_name: str
    job_title: str
    department: str
    contract_type: str
    salary_cost: float
    hired_at: date
    terminated_at: Optional[date] = None

class StaffCreate(StaffBase):
    company_id: Optional[UUID] = None

class StaffOut(StaffBase):
    id: UUID
    company_id: Optional[UUID] = None

    class Config:
        orm_mode = True

class FinancialStats(BaseModel):
    total_balance: float
    burn_rate: float
    headcount: int

