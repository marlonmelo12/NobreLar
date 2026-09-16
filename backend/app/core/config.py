"""Configurações centrais do sistema NobreLOG IA.

Gerencia variáveis de ambiente, caminhos de dados, parâmetros do solver
e credenciais de segurança via Pydantic Settings.
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Configurações da aplicação."""

    PROJECT_NAME: str = "NobreLOG IA — Montagem Automática de Carga por Eixo"
    VERSION: str = "3.0.0"
    API_V1_STR: str = "/api/v1"

    # Segurança e Autenticação JWT
    SECRET_KEY: str = "nobrelog-ia-super-secret-key-crateus-2026-hackathon"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 24 horas

    # Banco de Dados (SQLite por padrão para execução local imediata; PostgreSQL via env)
    DATABASE_URL: str = "sqlite:///./nobrelog.db"

    # Parâmetros Padrão do Solver OR-Tools CP-SAT
    SOLVER_TIME_LIMIT_SECONDS: float = 30.0
    SOLVER_NUM_SEARCH_WORKERS: int = 8

    # Parâmetros de Geocodificação e Roteamento
    NOMINATIM_USER_AGENT: str = "nobrelog_ia_ufc_crateus"
    OSRM_API_URL: str = "http://router.project-osrm.org"
    ENABLE_ONLINE_ROUTING: bool = False  # False para usar Haversine offline por padrão sem latência

    # Diretório dos Dados Brutos
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    DATA_RAW_DIR: Path = BASE_DIR.parent / "data" / "raw"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings = Settings()
