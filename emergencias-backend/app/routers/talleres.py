# ============================================================
# routers/talleres.py
#
# CONTEXTO DEL PROYECTO:
#   Plataforma Inteligente de Emergencias Vehiculares
#   Backend: FastAPI + PostgreSQL (Supabase)
#   Universidad Autónoma Gabriel René Moreno - SI2 2026
#
# CU3: Gestión de Talleres
#
# ENDPOINTS:
#   POST   /talleres/            → Registrar taller + usuario dueño (solo A4)
#   GET    /talleres/            → Listar todos los talleres (solo A4)
#   GET    /talleres/{id_taller} → Obtener taller por ID (solo A4)
#   PUT    /talleres/{id_taller} → Actualizar taller completo (solo A4)
#   PATCH  /talleres/{id_taller} → Actualizar campos parciales (solo A4)
#   DELETE /talleres/{id_taller} → Eliminar taller y su usuario dueño (solo A4)
#
# SEGURIDAD:
#   - Todos los endpoints requieren rol 'admin'
#   - Se reutiliza require_admin de usuarios.py
#
# LÓGICA DE REGISTRO:
#   Al crear un taller, se crean DOS registros en la BD:
#     1. Un Usuario con rol='taller' (tabla usuarios)
#     2. Un Taller vinculado a ese usuario (tabla talleres)
#   Al eliminar un taller, se elimina también su usuario dueño.
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.usuario import Usuario, TipoRol
from app.models.taller import Taller
from app.schemas.taller import TallerCreate, TallerUpdate, TallerOut
from app.utils.security import hash_password
from app.routers.auth import get_current_user

router = APIRouter(prefix="/talleres", tags=["CU3 - Gestión de Talleres"])


# -------------------------------------------------------
# Función auxiliar: verifica que el usuario sea admin
# Mismo patrón que en usuarios.py (require_admin)
# -------------------------------------------------------
def require_admin(current_user: Usuario = Depends(get_current_user)):
    if current_user.rol != TipoRol.admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso denegado: se requiere rol administrador"
        )
    return current_user


# -------------------------------------------------------
# Función auxiliar: convierte objeto Taller a TallerOut
# Se necesita porque TallerOut combina datos de dos tablas
# (talleres + usuarios) y from_attributes no alcanza.
# -------------------------------------------------------
def taller_a_schema(taller: Taller) -> TallerOut:
    return TallerOut(
        id_taller        = taller.id_taller,
        dueño_id         = taller.dueño_id,
        nombre_dueno     = taller.dueno.nombre,
        email_dueno      = taller.dueno.email,
        telefono_dueno   = taller.dueno.telefono,
        nombre_taller    = taller.nombre,
        direccion        = taller.direccion,
        nit              = taller.nit,
        latitud_decimal  = taller.latitud_decimal,
        longitud_decimal = taller.longitud_decimal,
    )


# -------------------------------------------------------
# POST /talleres/
# PRIVADO - Solo administrador (A4)
#
# Flujo:
#   1. Verifica que el email no esté registrado
#   2. Crea el Usuario con rol='taller'
#   3. Crea el Taller vinculado a ese usuario
#   4. Devuelve los datos combinados
# Para que quede así:
@router.post("/", response_model=TallerOut, status_code=status.HTTP_201_CREATED)
def registrar_taller(
    datos: TallerCreate,
    db: Session = Depends(get_db)
):
    # 1. Verificar que el email no esté ya registrado
    existe = db.query(Usuario).filter(Usuario.email == datos.email).first()
    if existe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado"
        )

    # 2. Crear el usuario dueño con rol 'taller'
    nuevo_usuario = Usuario(
        nombre        = datos.nombre_dueno,
        email         = datos.email,
        password_hash = hash_password(datos.password),
        telefono      = datos.telefono,
        rol           = TipoRol.taller
    )
    db.add(nuevo_usuario)
    db.flush()  # Genera el id_usuario sin hacer commit aún

    # 3. Crear el taller vinculado al usuario recién creado
    nuevo_taller = Taller(
        dueño_id         = nuevo_usuario.id_usuario,
        nombre           = datos.nombre_taller,
        direccion        = datos.direccion,
        nit              = datos.nit,
        latitud_decimal  = datos.latitud_decimal,
        longitud_decimal = datos.longitud_decimal,
    )
    db.add(nuevo_taller)
    db.commit()
    db.refresh(nuevo_taller)
    db.refresh(nuevo_usuario)

    return taller_a_schema(nuevo_taller)


# -------------------------------------------------------
# GET /talleres/
# PRIVADO - Solo administrador (A4)
# Devuelve la lista completa de talleres registrados
# -------------------------------------------------------
@router.get("/", response_model=List[TallerOut])
def listar_talleres(
    db: Session = Depends(get_db),
    _: Usuario  = Depends(require_admin)
):
    talleres = db.query(Taller).all()
    return [taller_a_schema(t) for t in talleres]


# -------------------------------------------------------
# GET /talleres/{id_taller}
# PRIVADO - Solo administrador (A4)
# Devuelve los datos de un taller específico por su ID
# -------------------------------------------------------
@router.get("/{id_taller}", response_model=TallerOut)
def obtener_taller(
    id_taller: int,
    db: Session = Depends(get_db),
    _: Usuario  = Depends(require_admin)
):
    taller = db.query(Taller).filter(Taller.id_taller == id_taller).first()
    if not taller:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Taller no encontrado"
        )
    return taller_a_schema(taller)


# -------------------------------------------------------
# PUT /talleres/{id_taller}
# PRIVADO - Solo administrador (A4)
# Actualización completa del taller
# Se deben enviar todos los campos
# -------------------------------------------------------
@router.put("/{id_taller}", response_model=TallerOut)
def actualizar_taller(
    id_taller: int,
    datos: TallerCreate,
    db: Session = Depends(get_db),
    _: Usuario  = Depends(require_admin)
):
    taller = db.query(Taller).filter(Taller.id_taller == id_taller).first()
    if not taller:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Taller no encontrado"
        )

    # Verificar que el nuevo email no pertenezca a otro usuario
    dueno = db.query(Usuario).filter(Usuario.id_usuario == taller.dueño_id).first()
    if datos.email != dueno.email:
        email_existe = db.query(Usuario).filter(Usuario.email == datos.email).first()
        if email_existe:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El email ya está en uso por otro usuario"
            )

    # Actualizar datos del usuario dueño
    dueno.nombre        = datos.nombre_dueno
    dueno.email         = datos.email
    dueno.password_hash = hash_password(datos.password)
    dueno.telefono      = datos.telefono

    # Actualizar datos del taller
    taller.nombre           = datos.nombre_taller
    taller.direccion        = datos.direccion
    taller.nit              = datos.nit
    taller.latitud_decimal  = datos.latitud_decimal
    taller.longitud_decimal = datos.longitud_decimal

    db.commit()
    db.refresh(taller)
    db.refresh(dueno)

    return taller_a_schema(taller)


# -------------------------------------------------------
# PATCH /talleres/{id_taller}
# PRIVADO - Solo administrador (A4)
# Actualización parcial: solo los campos que lleguen
# -------------------------------------------------------
@router.patch("/{id_taller}", response_model=TallerOut)
def actualizar_taller_parcial(
    id_taller: int,
    datos: TallerUpdate,
    db: Session = Depends(get_db),
    _: Usuario  = Depends(require_admin)
):
    taller = db.query(Taller).filter(Taller.id_taller == id_taller).first()
    if not taller:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Taller no encontrado"
        )

    dueno = db.query(Usuario).filter(Usuario.id_usuario == taller.dueño_id).first()

    # Actualizar solo los campos del taller que vengan
    if datos.nombre_taller    is not None: taller.nombre           = datos.nombre_taller
    if datos.direccion        is not None: taller.direccion        = datos.direccion
    if datos.nit              is not None: taller.nit              = datos.nit
    if datos.latitud_decimal  is not None: taller.latitud_decimal  = datos.latitud_decimal
    if datos.longitud_decimal is not None: taller.longitud_decimal = datos.longitud_decimal

    # Actualizar solo los campos del dueño que vengan
    if datos.nombre_dueno is not None: dueno.nombre   = datos.nombre_dueno
    if datos.telefono     is not None: dueno.telefono = datos.telefono

    db.commit()
    db.refresh(taller)
    db.refresh(dueno)

    return taller_a_schema(taller)


# -------------------------------------------------------
# DELETE /talleres/{id_taller}
# PRIVADO - Solo administrador (A4)
# Elimina el taller Y el usuario dueño asociado
# -------------------------------------------------------
@router.delete("/{id_taller}", status_code=status.HTTP_200_OK)
def eliminar_taller(
    id_taller: int,
    db: Session = Depends(get_db),
    _: Usuario  = Depends(require_admin)
):
    taller = db.query(Taller).filter(Taller.id_taller == id_taller).first()
    if not taller:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Taller no encontrado"
        )

    nombre_taller = taller.nombre

    # Eliminar primero el taller (para no violar FK)
    # luego el usuario dueño
    dueno = db.query(Usuario).filter(Usuario.id_usuario == taller.dueño_id).first()
    db.delete(taller)
    db.flush()

    if dueno:
        db.delete(dueno)

    db.commit()
    return {"message": f"Taller '{nombre_taller}' y su usuario dueño eliminados correctamente"}