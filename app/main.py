import logging
from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles

# --- CONFIGURAÇÃO DE BANCO DE DADOS ---
# Ajuste os imports abaixo conforme a estrutura real das suas pastas no The Limbo.
# Geralmente fica em app/core/database.py ou app/database.py
try:
    from app.core.database import engine, Base
except ImportError:
    # Fallback caso a estrutura de pastas seja diferente
    from app.database import engine, Base

# --- IMPORTAÇÃO DE MODELOS (CRUCIAL PARA O ORM) ---
# O SQLAlchemy precisa "ver" as classes dos modelos para criar as tabelas.
# Importe aqui os models de cada módulo que você tem.
try:
    from app.modules.auth import models as auth_models
    from app.modules.backbone import models as backbone_models
    from app.modules.growth import models as growth_models
    from app.modules.product import models as product_models
    from app.modules.cs import models as cs_models
    from app.modules.advisory import models as advisory_models
    from app.modules.agents import models as agents_models
    from app.modules.cockpit import models as cockpit_models
    from app.modules.reports import models as reports_models
    from app.modules.hub import models as hub_models
except ImportError:
    print("Aviso: Alguns modelos não puderam ser importados. Verifique os caminhos.")

# --- ROTAS ---
from app.modules.backbone.router import router as backbone_router
from app.modules.growth.router import router as growth_router
from app.modules.product.router import router as product_router
from app.modules.cs.router import router as cs_router
from app.modules.advisory.router import router as advisory_router
from app.modules.auth.router import router as auth_router
from app.modules.agents.router import router as agents_router
from app.modules.cockpit.router import router as cockpit_router
from app.modules.reports.router import router as reports_router
from app.modules.hub.router import router as hub_router

# --- SETUP DE LOGS ---
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("the_limbo_api")

app = FastAPI(title="THE LIMBO - Business OS")

templates = Jinja2Templates(directory="app/templates")

# Tenta montar estáticos se a pasta existir (opcional, mas boa prática)
try:
    app.mount("/static", StaticFiles(directory="app/static"), name="static")
except RuntimeError:
    pass

# --- EVENTO DE STARTUP (CRIAÇÃO DAS TABELAS) ---
@app.on_event("startup")
def startup_event():
    """
    Executa quando o The Limbo inicia.
    Cria as tabelas no banco de dados automaticamente.
    """
    logger.info("Verificando banco de dados do The Limbo...")
    try:
        # Cria todas as tabelas encontradas nos imports de models acima
        Base.metadata.create_all(bind=engine)
        logger.info("Tabelas criadas/verificadas com sucesso!")
        # Seed Sofia Education IA + BodyVision.IA
        try:
            from app.core.database import SessionLocal
            from app.modules.hub.service import ensure_products
            db = SessionLocal()
            ids = ensure_products(db)
            logger.info(f"Produtos hub: {list(ids.keys())}")
            db.close()
        except Exception as se:
            logger.warning(f"Hub seed skipped: {se}")
    except Exception as e:
        logger.error(f"Erro ao conectar ou criar tabelas: {e}")

# Registrando os módulos
app.include_router(backbone_router, prefix="/api/v1/backbone", tags=["Backbone (Finance/Ops)"])
app.include_router(growth_router, prefix="/api/v1/growth", tags=["Growth (Marketing)"])
app.include_router(product_router, prefix="/api/v1/product", tags=["Product (Roadmap)"])
app.include_router(cs_router, prefix="/api/v1/cs", tags=["CS (Customer Success)"])
app.include_router(advisory_router, prefix="/api/v1/advisory", tags=["AI Advisor"])
app.include_router(agents_router, prefix="/api/v1/agents", tags=["Multi-Agent HI-C"])
app.include_router(cockpit_router, prefix="/api/v1/cockpit", tags=["MVP Cockpit"])
app.include_router(reports_router, prefix="/api/v1/reports", tags=["App Reports (Primary)"])
app.include_router(hub_router, prefix="/api/v1/hub", tags=["Hub INPUT/OUTPUT"])
app.include_router(auth_router, prefix="/api/v1/auth", tags=["Authentication"])

@app.get("/")
def read_root():
    return RedirectResponse(url="/api/v1/cockpit/dashboard", status_code=302)

@app.get("/glossary")
def read_glossary(request: Request):
    return templates.TemplateResponse("dashboard/glossary.html", {"request": request})