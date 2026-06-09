# ============================================================
# routers/talleres.py
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
    # Acceso total temporal
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
        tenant_id        = taller.tenant_id,
    )


# -------------------------------------------------------
# POST /talleres/
@router.post("/", response_model=TallerOut, status_code=status.HTTP_201_CREATED)
def registrar_taller(
    datos: TallerCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    # 1. Verificar que el email no esté ya registrado
    existe = db.query(Usuario).filter(Usuario.email == datos.email).first()
    if existe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El email ya está registrado"
        )

    target_tenant_id = datos.tenant_id or (current_user.tenant_id if current_user else 1) or 1

    # 2. Crear el usuario dueño con rol 'taller'
    nuevo_usuario = Usuario(
        nombre        = datos.nombre_dueno,
        email         = datos.email,
        password_hash = hash_password(datos.password),
        telefono      = datos.telefono,
        rol           = TipoRol.taller,
        tenant_id     = target_tenant_id
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
        tenant_id        = target_tenant_id
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
    current_user: Usuario = Depends(require_admin)
):
    query = db.query(Taller)
    if current_user.tenant_id is not None:
        query = query.filter(Taller.tenant_id == current_user.tenant_id)
    talleres = query.all()
    return [taller_a_schema(t) for t in talleres]


# -------------------------------------------------------
# GET /talleres/cercanos
# PÚBLICO para clientes y técnicos
# Devuelve la lista completa de talleres para el mapa
# -------------------------------------------------------
@router.get("/cercanos", response_model=List[TallerOut])
def listar_talleres_cercanos(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    query = db.query(Taller)
    if current_user.tenant_id is not None:
        query = query.filter(Taller.tenant_id == current_user.tenant_id)
    talleres = query.all()
    return [taller_a_schema(t) for t in talleres]


# -------------------------------------------------------
# -------------------------------------------------------
# GET /talleres/{id_taller}
# PRIVADO - Solo administrador (A4)
# Devuelve los datos de un taller específico por su ID
# -------------------------------------------------------
@router.get("/{id_taller}", response_model=TallerOut)
def obtener_taller(
    id_taller: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(require_admin)
):
    taller = db.query(Taller).filter(Taller.id_taller == id_taller).first()
    if not taller:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Taller no encontrado"
        )
    if current_user.tenant_id is not None and taller.tenant_id != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No autorizado: El taller pertenece a otro tenant"
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
    current_user: Usuario  = Depends(require_admin)
):
    taller = db.query(Taller).filter(Taller.id_taller == id_taller).first()
    if not taller:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Taller no encontrado"
        )
    if current_user.tenant_id is not None and taller.tenant_id != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No autorizado: El taller pertenece a otro tenant"
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
    if datos.tenant_id is not None:
        dueno.tenant_id = datos.tenant_id

    # Actualizar datos del taller
    taller.nombre           = datos.nombre_taller
    taller.direccion        = datos.direccion
    taller.nit              = datos.nit
    taller.latitud_decimal  = datos.latitud_decimal
    taller.longitud_decimal = datos.longitud_decimal
    if datos.tenant_id is not None:
        taller.tenant_id = datos.tenant_id

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
    current_user: Usuario  = Depends(require_admin)
):
    taller = db.query(Taller).filter(Taller.id_taller == id_taller).first()
    if not taller:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Taller no encontrado"
        )
    if current_user.tenant_id is not None and taller.tenant_id != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No autorizado: El taller pertenece a otro tenant"
        )

    dueno = db.query(Usuario).filter(Usuario.id_usuario == taller.dueño_id).first()

    # Actualizar solo los campos del taller que vengan
    if datos.nombre_taller    is not None: taller.nombre           = datos.nombre_taller
    if datos.direccion        is not None: taller.direccion        = datos.direccion
    if datos.nit              is not None: taller.nit              = datos.nit
    if datos.latitud_decimal  is not None: taller.latitud_decimal  = datos.latitud_decimal
    if datos.longitud_decimal is not None: taller.longitud_decimal = datos.longitud_decimal
    if datos.tenant_id        is not None:
        taller.tenant_id = datos.tenant_id
        dueno.tenant_id  = datos.tenant_id

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
    current_user: Usuario  = Depends(require_admin)
):
    taller = db.query(Taller).filter(Taller.id_taller == id_taller).first()
    if not taller:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Taller no encontrado"
        )
    if current_user.tenant_id is not None and taller.tenant_id != current_user.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No autorizado: El taller pertenece a otro tenant"
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

# -------------------------------------------------------
# PATCH /talleres/mi-ubicacion/actualizar
# PRIVADO - Solo Taller (A2)
# Permite a un taller actualizar sus propias coordenadas
# -------------------------------------------------------
from pydantic import BaseModel
from decimal import Decimal

class UbicacionUpdate(BaseModel):
    latitud_decimal: Decimal
    longitud_decimal: Decimal

@router.patch("/mi-ubicacion/actualizar", response_model=TallerOut)
def actualizar_mi_ubicacion(
    datos: UbicacionUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user) # Obtenemos quién está logueado
):
    # Control de acceso eliminado temporalmente por petición del usuario

    # 2. Buscar el taller que le pertenece a este usuario
    taller = db.query(Taller).filter(Taller.dueño_id == current_user.id_usuario).first()
    if not taller:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No se encontró un taller asociado a tu cuenta."
        )

    # 3. Actualizar coordenadas
    taller.latitud_decimal = datos.latitud_decimal
    taller.longitud_decimal = datos.longitud_decimal

    db.commit()
    db.refresh(taller)
    
    return taller_a_schema(taller)
# -------------------------------------------------------
# GET /talleres/mi-taller/perfil
# PRIVADO - Solo Taller (A2)
# Devuelve los datos del taller autenticado para ver si tiene GPS
# -------------------------------------------------------
@router.get("/mi-taller/perfil", response_model=TallerOut)
def obtener_mi_taller(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.rol == "tecnico":
        from app.models.tecnico import Tecnico
        tecnico = db.query(Tecnico).filter(Tecnico.usuario_id == current_user.id_usuario).first()
        if not tecnico:
            raise HTTPException(status_code=404, detail="El técnico no está asignado a ningún taller.")
        taller = db.query(Taller).filter(Taller.id_taller == tecnico.taller_id).first()
    else:
        taller = db.query(Taller).filter(Taller.dueño_id == current_user.id_usuario).first()
        
    if not taller:
        raise HTTPException(status_code=404, detail="Taller no encontrado.")
    return taller_a_schema(taller)

# -------------------------------------------------------
# POST /talleres/inventario
# PRIVADO - Solo Taller
# Añade o suma cantidad a un repuesto
# -------------------------------------------------------
from app.models.taller import TallerInventario
from app.schemas.taller import InventarioCreate, InventarioOut

@router.post("/inventario", response_model=InventarioOut)
def agregar_inventario(
    datos: InventarioCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    taller = db.query(Taller).filter(Taller.dueño_id == current_user.id_usuario).first()
    if not taller:
        raise HTTPException(status_code=404, detail="No tienes un taller asignado.")
    
    # Buscar si ya existe el item
    item = db.query(TallerInventario).filter(
        TallerInventario.taller_id == taller.id_taller,
        TallerInventario.item_nombre == datos.item_nombre.lower()
    ).first()

    if item:
        item.cantidad += datos.cantidad
    else:
        item = TallerInventario(
            taller_id=taller.id_taller,
            item_nombre=datos.item_nombre.lower(),
            cantidad=datos.cantidad
        )
        db.add(item)
    
    db.commit()
    db.refresh(item)
    return item

# -------------------------------------------------------
# GET /talleres/inventario
# PRIVADO - Solo Taller
# Lista el inventario del taller
# -------------------------------------------------------
@router.get("/inventario", response_model=List[InventarioOut])
def listar_inventario(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    taller = db.query(Taller).filter(Taller.dueño_id == current_user.id_usuario).first()
    if not taller:
        raise HTTPException(status_code=404, detail="No tienes un taller asignado.")
    
    return db.query(TallerInventario).filter(TallerInventario.taller_id == taller.id_taller).all()