# ============================================================
# utils/security.py
# Funciones de seguridad reutilizables:
#   - Hashear y verificar contraseñas con bcrypt
#   - Crear y decodificar tokens JWT
# ============================================================

from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from app.config import SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES

# Contexto de encriptación usando bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


# -------------------------------------------------------
# Hashear una contraseña en texto plano
# -------------------------------------------------------
def hash_password(password: str) -> str:
    return pwd_context.hash(password)


# -------------------------------------------------------
# Verificar si una contraseña coincide con su hash
# -------------------------------------------------------
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# -------------------------------------------------------
# Crear un token JWT con el email y rol del usuario
# Expira según ACCESS_TOKEN_EXPIRE_MINUTES del .env
# -------------------------------------------------------
def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


# -------------------------------------------------------
# Decodificar un token JWT y retornar su contenido
# Retorna None si el token es inválido o expiró
# -------------------------------------------------------
def decode_access_token(token: str) -> dict | None:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None