# ============================================================
# routers/auth.py
# CU1: Gestionar Autenticación
#   POST /auth/login   → Inicia sesión, devuelve JWT
#   POST /auth/logout  → Cierra sesión (invalida el token)
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.usuario import Usuario
from app.schemas.usuario import LoginRequest, TokenResponse
from app.utils.security import verify_password, create_access_token, decode_access_token

router = APIRouter(prefix="/auth", tags=["CU1 - Autenticación"])

# Esquema OAuth2 para leer el token del header Authorization
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


# -------------------------------------------------------
# POST /auth/login
# Recibe email y contraseña, devuelve un token JWT
# -------------------------------------------------------
@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, db: Session = Depends(get_db)):

    # 1. Buscar el usuario por email
    usuario = db.query(Usuario).filter(Usuario.email == request.email).first()

    # 2. Verificar que existe y que la contraseña es correcta
    if not usuario or not verify_password(request.password, usuario.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas"
        )

    # 3. Generar el token con el email y rol del usuario
    token = create_access_token(data={
        "sub": usuario.email,
        "rol": usuario.rol
    })

    return TokenResponse(
        access_token=token,
        rol=usuario.rol,
        nombre=usuario.nombre
    )


# -------------------------------------------------------
# POST /auth/logout
# El cliente debe eliminar el token de su lado
# Aquí validamos que el token sea válido antes de cerrar
# -------------------------------------------------------
@router.post("/logout")
def logout(token: str = Depends(oauth2_scheme)):

    # Verificar que el token sea válido
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o ya expirado"
        )

    # En JWT stateless, el cierre de sesión lo maneja el cliente
    # borrando el token de su almacenamiento local
    return {"message": "Sesión cerrada correctamente"}


# -------------------------------------------------------
# Dependencia reutilizable: obtener el usuario autenticado
# Se importa en otros routers para proteger endpoints
# -------------------------------------------------------
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> Usuario:

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o expirado"
        )

    usuario = db.query(Usuario).filter(Usuario.email == payload.get("sub")).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    return usuario