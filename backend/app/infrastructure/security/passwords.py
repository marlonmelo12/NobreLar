"""Serviço de hash e verificação de senhas com bcrypt nativo.

Utiliza bcrypt diretamente para total compatibilidade com Python 3.11+
e eliminação de problemas de versão de bibliotecas legadas.
"""

import bcrypt


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se a senha em texto puro corresponde ao hash armazenado."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Gera o hash criptografado da senha com salt seguro."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")
