# ============================================================
# routers/usuarios.py
#
# CONTEXTO DEL PROYECTO:
#   Plataforma Inteligente de Emergencias Vehiculares
#   Backend: FastAPI + PostgreSQL (Supabase)
#
# CU2: Gestión de Clientes/Usuarios
#
# ENDPOINTS:
#   POST   /usuarios/registro     → Registro público desde login (A1, A2)
#   GET    /usuarios/             → Listar todos los usuarios (solo A4)
#   GET    /usuarios/{id}         → Ver un usuario por ID (solo A4)
#   PUT    /usuarios/{id}         → Actualizar usuario completo (solo A4)
#   PATCH  /usuarios/{id}         → Actualizar campos parciales (solo A4)
#   DELETE /usuarios/{id}         → Eliminar usuario (solo A4)
#
# SEGURIDAD:
#   - El registro es público (no requiere token)
#   - Todas las demás operaciones requieren rol 'admin'
#   - Se usa get_current_user de auth.py para validar el token
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.usuario import Usuario, TipoRol
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate, UsuarioOut
from app.utils.security import hash_password
from app.routers.auth import get_current_user

router = APIRouter(prefix="/usuarios", tags=["CU2 - Gestión de Usuarios"])


# -------------------------------------------------------
# Función auxiliar: verifica que el usuario sea admin
# Se reutiliza en todos los endpoints protegidos de este router
# -------------------------------------------------------
def require_admin(current_user: Usuario = Depends(get_current_user)):
    if current_user.rol != TipoRol.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado: se requiere rol administrador"
        )
    return current_user


# -------------------------------------------------------
# POST /usuarios/registro
# PÚBLICO - No requiere token
# Permite que un Cliente o Taller se registre desde el login
# El rol por defecto es 'cliente', para registrar otros
# roles debe hacerlo el administrador desde el CRUD
# -------------------------------------------------------
@router.post("/registro", response_model=UsuarioOut, status_code=status.HTTP_201_CREATED)
def registrar_usuario(datos: UsuarioCreate, db: Session = Depends(get_db)):

    # 1. Verificar que el email no esté ya registrado
    existe = db.query(Usuario).filter(Usuario.email == datos.email).first()
    if existe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado"
        )

    # 2. Crear el nuevo usuario hasheando la contraseña
    nuevo_usuario = Usuario(
        nombre        = datos.nombre,
        email         = datos.email,
        password_hash = hash_password(datos.password),
        telefono      = datos.telefono,
        rol           = "admin"
    )

    # 3. Guardar en la base de datos
    db.add(nuevo_usuario)
    db.commit()
    db.refresh(nuevo_usuario)

    return nuevo_usuario


# -------------------------------------------------------
# GET /usuarios/
# PRIVADO - Solo administrador (A4)
# Devuelve la lista completa de usuarios registrados
# -------------------------------------------------------
@router.get("/", response_model=List[UsuarioOut])
def listar_usuarios(
    db: Session = Depends(get_db),
    _: Usuario  = Depends(require_admin)
):
    return db.query(Usuario).all()


# -------------------------------------------------------
# GET /usuarios/{id_usuario}
# PRIVADO - Solo administrador (A4)
# Devuelve los datos de un usuario específico por su ID
# -------------------------------------------------------
@router.get("/{id_usuario}", response_model=UsuarioOut)
def obtener_usuario(
    id_usuario: int,
    db: Session        = Depends(get_db),
    _: Usuario         = Depends(require_admin)
):
    usuario = db.query(Usuario).filter(Usuario.id_usuario == id_usuario).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )
    return usuario


# -------------------------------------------------------
# PUT /usuarios/{id_usuario}
# PRIVADO - Solo administrador (A4)
# Actualización completa de un usuario
# Se deben enviar todos los campos
# -------------------------------------------------------
@router.put("/{id_usuario}", response_model=UsuarioOut)
def actualizar_usuario(
    id_usuario: int,
    datos: UsuarioCreate,
    db: Session        = Depends(get_db),
    _: Usuario         = Depends(require_admin)
):
    usuario = db.query(Usuario).filter(Usuario.id_usuario == id_usuario).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    # Verificar que el nuevo email no pertenezca a otro usuario
    if datos.email != usuario.email:
        email_existe = db.query(Usuario).filter(Usuario.email == datos.email).first()
        if email_existe:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está en uso por otro usuario"
            )

    # Actualizar todos los campos
    usuario.nombre        = datos.nombre
    usuario.email         = datos.email
    usuario.password_hash = hash_password(datos.password)
    usuario.telefono      = datos.telefono
    usuario.rol           = datos.rol

    db.commit()
    db.refresh(usuario)
    return usuario


# -------------------------------------------------------
# PATCH /usuarios/{id_usuario}
# PRIVADO - Solo administrador (A4)
# Actualización parcial: solo se actualizan los campos
# que vengan en el body, los demás quedan igual
# -------------------------------------------------------
@router.patch("/{id_usuario}", response_model=UsuarioOut)
def actualizar_usuario_parcial(
    id_usuario: int,
    datos: UsuarioUpdate,
    db: Session        = Depends(get_db),
    _: Usuario         = Depends(require_admin)
):
    usuario = db.query(Usuario).filter(Usuario.id_usuario == id_usuario).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    # Solo actualiza los campos que no sean None
    if datos.nombre   is not None: usuario.nombre        = datos.nombre
    if datos.telefono is not None: usuario.telefono      = datos.telefono
    if datos.rol      is not None: usuario.rol           = datos.rol
    if datos.password is not None: usuario.password_hash = hash_password(datos.password)
    if datos.email    is not None:
        email_existe = db.query(Usuario).filter(Usuario.email == datos.email).first()
        if email_existe and email_existe.id_usuario != id_usuario:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está en uso por otro usuario"
            )
        usuario.email = datos.email

    db.commit()
    db.refresh(usuario)
    return usuario


# -------------------------------------------------------
# DELETE /usuarios/{id_usuario}
# PRIVADO - Solo administrador (A4)
# Elimina un usuario por su ID
# No se puede eliminar a sí mismo el administrador
# -------------------------------------------------------
@router.delete("/{id_usuario}", status_code=status.HTTP_200_OK)
def eliminar_usuario(
    id_usuario: int,
    db: Session        = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    # Evitar que el admin se elimine a sí mismo
    if current_user.id_usuario == id_usuario:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No puedes eliminar tu propia cuenta"
        )

    usuario = db.query(Usuario).filter(Usuario.id_usuario == id_usuario).first()
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuario no encontrado"
        )

    db.delete(usuario)
    db.commit()
    return {"message": f"Usuario '{usuario.nombre}' eliminado correctamente"}