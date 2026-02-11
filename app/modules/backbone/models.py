from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime, Date, Numeric, Text, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.core.database import Base
import uuid
from datetime import datetime

class BankAccount(Base):
    __tablename__ = "backbone_bank_accounts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"))
    bank_name = Column(String)
    account_type = Column(String)
    current_balance = Column(Numeric)
    currency = Column(String)

class CostCenter(Base):
    __tablename__ = "backbone_cost_centers"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"))
    name = Column(String)
    code = Column(String)
    budget_limit = Column(Numeric)
    created_at = Column(DateTime, default=datetime.utcnow)

class Ledger(Base):
    __tablename__ = "backbone_ledger"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"))
    cost_center_id = Column(UUID(as_uuid=True), ForeignKey("backbone_cost_centers.id"))
    account_id = Column(UUID(as_uuid=True), ForeignKey("backbone_bank_accounts.id"))
    
    transaction_date = Column(Date)
    description = Column(Text)
    amount = Column(Numeric)
    type = Column(String) # opex, capex, revenue, cogs
    is_recurring = Column(Boolean, default=False)
    recurrence_period = Column(String) # monthly, yearly
    status = Column(String) # pending, paid
    document_url = Column(Text)
    external_transaction_id = Column(String)
    
    created_at = Column(DateTime, default=datetime.utcnow)

class Staff(Base):
    __tablename__ = "backbone_staff"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"))
    full_name = Column(String)
    job_title = Column(String)
    department = Column(String)
    contract_type = Column(String) # clt, pj, contractor
    salary_cost = Column(Numeric)
    hired_at = Column(Date)
    terminated_at = Column(Date)

class SubscriptionHistory(Base):
    __tablename__ = "finance_subscription_history"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    company_id = Column(UUID(as_uuid=True), ForeignKey("companies.id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    status = Column(String)
    plan_name = Column(String)
    mrr_amount = Column(Numeric)
    started_at = Column(DateTime)
    ended_at = Column(DateTime)
    change_type = Column(String) # upgrade, downgrade, churn
    previous_mrr_amount = Column(Numeric)
