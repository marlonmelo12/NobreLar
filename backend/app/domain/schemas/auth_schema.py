"""Esquemas Pydantic v2 para autenticação e tokens JWT."""

from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Contrato para solicitação de login de usuário."""
    username: str = Field(..., description="Nome de usuário (operador, aprovador ou admin)")
    password: str = Field(..., description="Senha em texto puro")


class TokenResponse(BaseModel):
    """Contrato de resposta com token JWT e permissões RBAC."""
    access_token: str = Field(..., description="Token de autenticação JWT Bearer")
    token_type: str = Field("bearer", description="Tipo do token de autorização")
    role: str = Field(..., description="Papel do usuário no sistema: operador, aprovador ou admin")
    username: str = Field(..., description="Nome do usuário autenticado")
