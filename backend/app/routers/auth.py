# ============================================================
# routers/auth.py
# CU1: Gestionar Autenticación
#   POST /auth/login   → Inicia sesión, devuelve JWT
#   POST /auth/logout  → Cierra sesión (invalida el token)
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from app.database import get_db
from app.models.usuario import Usuario, TipoRol
from app.models.taller import Taller
from app.models.tenant import Tenant
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

    usuario = db.query(Usuario).filter(Usuario.email == request.email).first()

    if not usuario or not verify_password(request.password, usuario.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciales incorrectas"
        )

    # Verificar si el tenant del usuario está suspendido
    if usuario.tenant_id is not None:
        tenant = db.query(Tenant).filter(Tenant.id_tenant == usuario.tenant_id).first()
        if tenant and tenant.estado == "suspendido":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Su empresa se encuentra suspendida. Contacte al administrador de la plataforma."
            )

    id_taller_encontrado = None
    if usuario.rol == TipoRol.taller:
        taller = db.query(Taller).filter(Taller.dueño_id == usuario.id_usuario).first()
        if taller:
            id_taller_encontrado = taller.id_taller

    token = create_access_token(data={
        "sub": usuario.email,
        "rol": usuario.rol,
        "tenant_id": usuario.tenant_id
    })

    return TokenResponse(
        access_token=token,
        token_type="bearer",
        rol=usuario.rol,
        nombre=usuario.nombre,
        id_usuario=usuario.id_usuario,  # 👈 ESTO ES LO QUE FALTA
        id_taller=id_taller_encontrado,
        tenant_id=usuario.tenant_id
    )


# -------------------------------------------------------
# POST /auth/logout
# El cliente debe eliminar el token de su lado
# Aquí validamos que el token sea válido antes de cerrar
# -------------------------------------------------------
@router.post("/logout")
def logout(token: str = Depends(oauth2_scheme)):

    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido o ya expirado"
        )

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