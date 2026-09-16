"""Injeção de dependências para as rotas da API FastAPI."""

from app.infrastructure.database.session import get_db
from app.infrastructure.security.jwt import get_current_user, require_role

__all__ = ["get_db", "get_current_user", "require_role"]
