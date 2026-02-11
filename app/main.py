from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from app.modules.backbone.router import router as backbone_router
from app.modules.growth.router import router as growth_router
from app.modules.product.router import router as product_router
from app.modules.cs.router import router as cs_router
from app.modules.advisory.router import router as advisory_router
from app.modules.auth.router import router as auth_router

app = FastAPI(title="THE LIMBO - Business OS")

templates = Jinja2Templates(directory="app/templates")

# Registrando os módulos
app.include_router(backbone_router, prefix="/api/v1/backbone", tags=["Backbone (Finance/Ops)"])
app.include_router(growth_router, prefix="/api/v1/growth", tags=["Growth (Marketing)"])
app.include_router(product_router, prefix="/api/v1/product", tags=["Product (Roadmap)"])
app.include_router(cs_router, prefix="/api/v1/cs", tags=["CS (Customer Success)"])
app.include_router(advisory_router, prefix="/api/v1/advisory", tags=["AI Advisor"])
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])

@app.get("/")
def read_root(request: Request):
    return templates.TemplateResponse("dashboard/index.html", {"request": request})

@app.get("/glossary")
def read_glossary(request: Request):
    return templates.TemplateResponse("dashboard/glossary.html", {"request": request})
