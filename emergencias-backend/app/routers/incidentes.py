# ============================================================
# routers/incidentes.py
#
# CU7: Registrar Emergencia Multimodal
#
# FLUJO SEGURO IMPLEMENTADO:
#   1. Valida propiedad del vehículo.
#   2. Crea el Incidente.
#   3. Hace un flush() para obtener el ID sin afectar la BD.
#   4. Crea el registro en el Historial con el ID obtenido.
#   5. Recorre y guarda las fotos/audios en Evidencias.
#   6. Aplica el commit(). Si algo falla, NO se guarda nada.
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.usuario import Usuario
from app.models.vehiculo import Vehiculo
from app.models.incidente import Incidente, EvidenciaIA, HistorialEstado, EstadoIncidente
from app.schemas.incidente import IncidenteCreate, IncidenteOut
from app.routers.auth import get_current_user

router = APIRouter(prefix="/incidentes", tags=["CU7 - Registrar Emergencia Multimodal"])

@router.post("/", response_model=IncidenteOut, status_code=status.HTTP_201_CREATED)
def registrar_emergencia(
    datos: IncidenteCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user) # Solo usuarios con Token (Cliente A1)
):
    # 1. SEGURIDAD: Verificar que el vehículo le pertenece al cliente logueado
    vehiculo = db.query(Vehiculo).filter(
        Vehiculo.id_vehiculo == datos.vehiculo_id,
        Vehiculo.usuario_id == current_user.id_usuario
    ).first()

    if not vehiculo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Operación denegada: El vehículo no existe o no te pertenece."
        )

    # 2. TABLA 1: Crear el Incidente base
    nuevo_incidente = Incidente(
        cliente_id          = current_user.id_usuario,
        vehiculo_id         = datos.vehiculo_id,
        latitud_emergencia  = datos.latitud_emergencia,
        longitud_emergencia = datos.longitud_emergencia,
        descripcion_texto   = datos.descripcion_texto
        # El estado y la prioridad se ponen solos por defecto según el modelo
    )
    db.add(nuevo_incidente)
    
    # MAGIA AQUI: flush() asigna un ID a 'nuevo_incidente' sin guardarlo definitivamente aún
    db.flush() 

    # 3. TABLA 2: Registrar el primer paso en el Historial de Trazabilidad
    historial_inicial = HistorialEstado(
        incidente_id     = nuevo_incidente.id_incidente,
        estado_incidente = EstadoIncidente.pendiente,
        comentario_texto = "Emergencia reportada inicialmente desde la aplicación móvil."
    )
    db.add(historial_inicial)

    # 4. TABLA 3: Guardar las evidencias (audios, fotos) iterando la lista enviada
    if datos.evidencias:
        for ev in datos.evidencias:
            nueva_evidencia = EvidenciaIA(
                incidente_id = nuevo_incidente.id_incidente,
                tipo_enum    = ev.tipo_enum,
                url_recurso  = ev.url_recurso
            )
            db.add(nueva_evidencia)

    # 5. Todo salió bien, confirmamos la transacción a la base de datos
    db.commit()
    db.refresh(nuevo_incidente)

    return nuevo_incidente

# -------------------------------------------------------
# GET /incidentes/mis-emergencias
# Opcional pero muy útil para el Frontend Responsivo (Listado)
# -------------------------------------------------------
@router.get("/mis-emergencias", response_model=List[IncidenteOut])
def listar_mis_emergencias(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Ordenamos por fecha descendente (la más reciente primero)
    emergencias = db.query(Incidente).filter(
        Incidente.cliente_id == current_user.id_usuario
    ).order_by(Incidente.fecha_creacion_timestamp.desc()).all()
    
    return emergencias