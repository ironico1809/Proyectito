# ============================================================
# routers/saas.py
# SaaS Administration & Registration Endpoints
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr
from typing import List, Optional

from app.database import get_db
from app.models.tenant import Tenant
from app.models.usuario import Usuario, TipoRol
from app.models.taller import Taller
from app.routers.auth import get_current_user
from app.utils.security import hash_password, verify_password, create_access_token
from app.schemas.usuario import TokenResponse
from app.schemas.tenant import TenantOut

router = APIRouter(prefix="/saas", tags=["SaaS Platform Administration"])

# -------------------------------------------------------
# Input Schemas
# -------------------------------------------------------
class RegistroSaaSInput(BaseModel):
    nombre_empresa: str
    descripcion_empresa: Optional[str] = None
    admin_nombre: str
    admin_email: EmailStr
    admin_password: str
    admin_telefono: Optional[str] = None

class TenantStatsOut(BaseModel):
    id_tenant: int
    nombre: str
    descripcion: Optional[str] = None
    estado: str
    talleres_count: int
    usuarios_count: int

class TenantEstadoUpdate(BaseModel):
    estado: str  # "activo" o "suspendido"

# -------------------------------------------------------
# Endpoint: POST /saas/registro-saas
# PÚBLICO: Crea Tenant + Admin y devuelve token de login
# -------------------------------------------------------
@router.post("/registro-saas", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def registro_saas(datos: RegistroSaaSInput, db: Session = Depends(get_db)):
    # 1. Validaciones
    empresa_existe = db.query(Tenant).filter(Tenant.nombre == datos.nombre_empresa).first()
    if empresa_existe:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El nombre de la empresa ya está en uso."
        )

    email_existe = db.query(Usuario).filter(Usuario.email == datos.admin_email).first()

    # Si el usuario ya existe, no permitimos asociar si es superadmin
    if email_existe:
        if email_existe.rol == TipoRol.superadmin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No se puede asociar una cuenta de Superadministrador a una red de talleres."
            )

    try:
        # 2. Crear Tenant
        nuevo_tenant = Tenant(
            nombre=datos.nombre_empresa,
            descripcion=datos.descripcion_empresa,
            estado="activo"
        )
        db.add(nuevo_tenant)
        db.commit()
        db.refresh(nuevo_tenant)

        # 3. Asociar o Crear Usuario Administrador para el Tenant
        if email_existe:
            # Reutilizamos el usuario existente: lo movemos al nuevo tenant, cambiamos su rol a admin y actualizamos su contraseña
            nuevo_admin = email_existe
            nuevo_admin.tenant_id = nuevo_tenant.id_tenant
            nuevo_admin.rol = TipoRol.admin
            nuevo_admin.password_hash = hash_password(datos.admin_password)
            # Si envió un nuevo nombre o teléfono, los actualizamos
            if datos.admin_nombre:
                nuevo_admin.nombre = datos.admin_nombre
            if datos.admin_telefono:
                nuevo_admin.telefono = datos.admin_telefono
        else:
            # Creamos un nuevo usuario desde cero
            nuevo_admin = Usuario(
                nombre=datos.admin_nombre,
                email=datos.admin_email,
                password_hash=hash_password(datos.admin_password),
                telefono=datos.admin_telefono,
                rol=TipoRol.admin,
                tenant_id=nuevo_tenant.id_tenant
            )
            db.add(nuevo_admin)

        db.commit()
        db.refresh(nuevo_admin)

        # 4. Generar Token JWT
        token = create_access_token(data={
            "sub": nuevo_admin.email,
            "rol": nuevo_admin.rol,
            "tenant_id": nuevo_admin.tenant_id
        })

        return TokenResponse(
            access_token=token,
            token_type="bearer",
            rol=nuevo_admin.rol,
            nombre=nuevo_admin.nombre,
            id_usuario=nuevo_admin.id_usuario,
            id_taller=None,
            tenant_id=nuevo_admin.tenant_id
        )

    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al registrar la empresa: {str(e)}"
        )

# -------------------------------------------------------
# Endpoint: GET /saas/tenants
# EXCLUSIVO: Solo accesible para el rol superadmin
# -------------------------------------------------------
@router.get("/tenants", response_model=List[TenantStatsOut])
def listar_tenants_con_metricas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.rol != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso restringido. Solo el Superadministrador puede acceder a esta información."
        )

    tenants = db.query(Tenant).order_by(Tenant.id_tenant.asc()).all()
    resultado = []

    for t in tenants:
        talleres_count = db.query(Taller).filter(Taller.tenant_id == t.id_tenant).count()
        usuarios_count = db.query(Usuario).filter(Usuario.tenant_id == t.id_tenant).count()
        resultado.append(TenantStatsOut(
            id_tenant=t.id_tenant,
            nombre=t.nombre,
            descripcion=t.descripcion,
            estado=t.estado,
            talleres_count=talleres_count,
            usuarios_count=usuarios_count
        ))

    return resultado

# -------------------------------------------------------
# Endpoint: PATCH /saas/tenants/{id}/estado
# EXCLUSIVO: Activa/suspende un tenant (Superadmin)
# -------------------------------------------------------
@router.patch("/tenants/{id_tenant}/estado", response_model=TenantOut)
def actualizar_estado_tenant(
    id_tenant: int,
    datos: TenantEstadoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.rol != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso restringido. Solo el Superadministrador puede realizar esta acción."
        )

    tenant = db.query(Tenant).filter(Tenant.id_tenant == id_tenant).first()
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Empresa no encontrada."
        )

    if datos.estado not in ["activo", "suspendido"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Estado inválido. Debe ser 'activo' o 'suspendido'."
        )

    tenant.estado = datos.estado
    db.commit()
    db.refresh(tenant)
    return tenant

# -------------------------------------------------------
# Endpoint: GET /saas/dashboard
# EXCLUSIVO: Métricas globales para el Superadmin
# -------------------------------------------------------
class SuperadminDashboardOut(BaseModel):
    total_tenants: int
    total_talleres: int
    total_usuarios: int
    total_incidentes: int
    total_ingresos: float

@router.get("/dashboard", response_model=SuperadminDashboardOut)
def obtener_dashboard_global(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    if current_user.rol != "superadmin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acceso restringido."
        )

    from sqlalchemy import func
    from app.models.incidente import Incidente
    from app.models.pago import Pago

    total_tenants = db.query(Tenant).count()
    total_talleres = db.query(Taller).count()
    total_usuarios = db.query(Usuario).count()
    total_incidentes = db.query(Incidente).count()
    
    total_ingresos = db.query(func.coalesce(func.sum(Pago.monto_total_decimal), 0)).scalar()

    return SuperadminDashboardOut(
        total_tenants=total_tenants,
        total_talleres=total_talleres,
        total_usuarios=total_usuarios,
        total_incidentes=total_incidentes,
        total_ingresos=float(total_ingresos)
    )
