"""Ponto de entrada principal da aplicação FastAPI do sistema NobreLOG IA.

Configura:
- Inicialização automática do banco de dados e dados semente (lifespan)
- Middleware de CORS para integração com o frontend React/Vite
- Roteamento completo para os módulos de autenticação, dados, otimização e relatórios
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog

from app.core.config import settings
from app.infrastructure.database.session import SessionLocal
from app.infrastructure.database.init_db import init_db
from app.services.ingest_service import IngestService

from app.api.routes.auth import router as auth_router
from app.api.routes.vehicles import router as vehicles_router
from app.api.routes.profiles import router as profiles_router
from app.api.routes.orders import router as orders_router
from app.api.routes.uploads import router as uploads_router
from app.api.routes.loads import router as loads_router
from app.api.routes.analytics import router as analytics_router

logger = structlog.get_logger()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gerencia o ciclo de vida da aplicação: inicializa e popula o banco de dados no startup."""
    logger.info("Iniciando NobreLOG IA — Montagem Automática de Carga por Eixo...")
    db = SessionLocal()
    try:
        init_db(db)
        # Se não houver pedidos no banco, executa ingestão automática dos arquivos brutos
        from app.domain.models import Order
        if db.query(Order).count() == 0:
            logger.info("Banco sem pedidos. Disparando ingestão automática dos arquivos brutos...")
            ingest_svc = IngestService(db)
            ingest_svc.ingest_all_raw_files()
    except Exception as e:
        logger.error(f"Erro na inicialização do banco: {e}")
    finally:
        db.close()
    yield
    logger.info("Encerrando NobreLOG IA.")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Sistema de Montagem Automática de Cargas Rodoviárias por Eixo com Solver OR-Tools CP-SAT e TSP.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configuração de CORS para permitir requisições do frontend React/Vite
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Inclusão dos roteadores tanto no prefixo versionado /api/v1 quanto no canônico /api
for prefix in [settings.API_V1_STR, "/api"]:
    app.include_router(auth_router, prefix=prefix)
    app.include_router(vehicles_router, prefix=prefix)
    app.include_router(profiles_router, prefix=prefix)
    app.include_router(orders_router, prefix=prefix)
    app.include_router(uploads_router, prefix=prefix)
    app.include_router(loads_router, prefix=prefix)
    app.include_router(analytics_router, prefix=prefix)


@app.get("/", summary="Boas-vindas")
def root():
    return {
        "mensagem": "NobreLOG IA — API Operacional Ativa",
        "documentacao": "/docs",
        "versao": settings.VERSION
    }
