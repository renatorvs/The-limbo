from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from app.core.database import get_db
from . import schemas, models, service

router = APIRouter()
templates = Jinja2Templates(directory="app/templates")

@router.get("/dashboard")
def view_dashboard(request: Request, db: Session = Depends(get_db)):
    stats = service.get_dashboard_stats(db)
    customers = service.get_customers(db)
    return templates.TemplateResponse("dashboard/cs.html", {
        "request": request,
        "stats": stats,
        "customers": customers
    })

@router.post("/customer", response_model=schemas.CustomerOut)
def create_customer(customer: schemas.CustomerCreate, db: Session = Depends(get_db)):
    return service.create_customer(db, customer)

@router.get("/customer", response_model=list[schemas.CustomerOut])
def get_customers(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return service.get_customers(db, skip, limit)

@router.post("/ticket", response_model=schemas.TicketOut)
def create_ticket(ticket: schemas.TicketCreate, db: Session = Depends(get_db)):
    db_ticket = models.Ticket(**ticket.dict())
    db.add(db_ticket)
    db.commit()
    db.refresh(db_ticket)
    return db_ticket
