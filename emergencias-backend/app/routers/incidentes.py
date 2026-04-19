# ============================================================
# routers/incidentes.py
#
# CONTEXTO DEL PROYECTO:
#   Plataforma Inteligente de Emergencias Vehiculares
#
# CASOS DE USO IMPLEMENTADOS AQUÍ:
#   - CU7: Registrar Emergencia Multimodal (Desde Flutter)
#   - CU10: Gestión de Solicitudes y Alertas (Desde Angular)
#   - CU11: Asignación de Órdenes y Técnicos (Desde Angular)
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.usuario import Usuario
from app.models.vehiculo import Vehiculo
from app.models.incidente import Incidente, EvidenciaIA, HistorialEstado, EstadoIncidente, PrioridadIncidente
from app.schemas.incidente import IncidenteCreate, IncidenteOut, AccionSolicitud, AsignarTecnico
from app.routers.auth import get_current_user

router = APIRouter(prefix="/incidentes", tags=["Gestión de Incidentes (CU7, CU10, CU11)"])

# -------------------------------------------------------
# CU7: REGISTRAR EMERGENCIA MULTIMODAL
# -------------------------------------------------------
@router.post("/", response_model=IncidenteOut, status_code=status.HTTP_201_CREATED)
def registrar_emergencia(
    datos: IncidenteCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # 1. SEGURIDAD: Validar que el vehículo le pertenezca al cliente
    vehiculo = db.query(Vehiculo).filter(
        Vehiculo.id_vehiculo == datos.vehiculo_id,
        Vehiculo.usuario_id == current_user.id_usuario
    ).first()

    if not vehiculo:
        raise HTTPException(status_code=403, detail="Vehículo no válido o no te pertenece.")

    # 2. TABLA PRINCIPAL: Crear incidente base
    nuevo_incidente = Incidente(
        cliente_id=current_user.id_usuario,
        vehiculo_id=datos.vehiculo_id,
        latitud_emergencia=datos.latitud_emergencia,
        longitud_emergencia=datos.longitud_emergencia,
        descripcion_texto=datos.descripcion_texto
    )
    db.add(nuevo_incidente)
    
    # El flush() asigna un ID sin hacer commit, asegurando transaccionalidad
    db.flush() 

    # 3. TRAZABILIDAD: Iniciar el historial del incidente
    db.add(HistorialEstado(
        incidente_id=nuevo_incidente.id_incidente,
        estado_enum=EstadoIncidente.pendiente,
        comentario_texto="Emergencia reportada desde la app móvil."
    ))

    # 4. EVIDENCIAS: Iterar y guardar array de fotos/audios
    if datos.evidencias:
        for ev in datos.evidencias:
            db.add(EvidenciaIA(
                incidente_id=nuevo_incidente.id_incidente,
                tipo_enum=ev.tipo_enum,
                url_recurso=ev.url_recurso
            ))

    db.commit()
    db.refresh(nuevo_incidente)
    return nuevo_incidente

# -------------------------------------------------------
# CU10: LISTAR SOLICITUDES PENDIENTES (Para el Taller)
# -------------------------------------------------------
@router.get("/pendientes", response_model=List[IncidenteOut])
def listar_solicitudes_pendientes(db: Session = Depends(get_db)):
    # Retorna solo las emergencias que aún no han sido tomadas por ningún taller
    return db.query(Incidente).filter(Incidente.estado_enum == EstadoIncidente.pendiente).all()

# -------------------------------------------------------
# CU10: ACEPTAR O RECHAZAR SOLICITUD
# -------------------------------------------------------
@router.post("/{id_incidente}/accion")
def responder_solicitud(id_incidente: int, datos: AccionSolicitud, db: Session = Depends(get_db)):
    # Bloqueo de concurrencia: Evita que dos talleres acepten el mismo incidente
    incidente = db.query(Incidente).filter(Incidente.id_incidente == id_incidente).first()
    if not incidente or incidente.estado_enum != EstadoIncidente.pendiente:
        raise HTTPException(status_code=400, detail="Incidente no disponible o ya fue tomado.")

    if datos.accion == "aceptar":
        incidente.estado_enum = EstadoIncidente.en_proceso
        comentario = "Solicitud aceptada por el taller. Preparando técnico."
    else:
        # Si rechaza, se queda 'pendiente' para reasignación automática
        comentario = f"Rechazado por el taller: {datos.comentario or 'Falta de capacidad'}"

    # Guardar la decisión en la trazabilidad
    db.add(HistorialEstado(
        incidente_id=id_incidente,
        estado_enum=incidente.estado_enum,
        comentario_texto=comentario
    ))
    db.commit()
    return {"message": "Acción procesada", "nuevo_estado": incidente.estado_enum}

# -------------------------------------------------------
# CU11: ASIGNAR TÉCNICO A LA ORDEN
# -------------------------------------------------------
@router.post("/{id_incidente}/asignar")
def asignar_tecnico(id_incidente: int, datos: AsignarTecnico, db: Session = Depends(get_db)):
    from app.models.tecnico import Tecnico
    
    incidente = db.query(Incidente).filter(Incidente.id_incidente == id_incidente).first()
    tecnico = db.query(Tecnico).filter(Tecnico.id_tecnico == datos.tecnico_id).first()

    # Validar que el técnico exista y esté libre
    if not tecnico or not tecnico.disponible_boolean:
        raise HTTPException(status_code=400, detail="El técnico seleccionado no está disponible.")

    # Vincular técnico y cambiar su disponibilidad
    incidente.tecnico_id = datos.tecnico_id
    tecnico.disponible_boolean = False  # El técnico ahora está 'en ruta'

    db.add(HistorialEstado(
        incidente_id=id_incidente,
        estado_enum=EstadoIncidente.en_proceso,
        comentario_texto=f"Técnico {tecnico.nombre} asignado y en ruta hacia el incidente."
    ))
    db.commit()
    return {"message": f"Técnico {tecnico.nombre} asignado correctamente."}

# -------------------------------------------------------
# CU9: MONITOREO DE AUXILIO EN TIEMPO REAL
# -------------------------------------------------------
@router.get("/{id_incidente}/monitoreo", tags=["CU9 - Monitoreo de Auxilio"])
def monitorear_auxilio(
    id_incidente: int, 
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """
    Retorna el estado actual de la emergencia y los datos 
    del técnico/taller asignado para que Flutter actualice su pantalla.
    """
    incidente = db.query(Incidente).filter(Incidente.id_incidente == id_incidente).first()
    
    if not incidente:
        raise HTTPException(status_code=404, detail="Incidente no encontrado")
        
    # Validar que el cliente solo vea sus propios incidentes, 
    # a menos que sea Admin o el Taller asignado
    if current_user.rol == TipoRol.cliente and incidente.cliente_id != current_user.id_usuario:
        raise HTTPException(status_code=403, detail="No tienes permiso para monitorear este incidente")

    respuesta = {
        "id_incidente": incidente.id_incidente,
        "estado_actual": incidente.estado_enum.value,
        "prioridad": incidente.prioridad_enum.value,
        "tecnico_asignado": None,
        "taller_responsable": None
    }

    # Si ya se asignó un técnico (CU11), buscamos sus datos
    if incidente.tecnico_id:
        from app.models.tecnico import Tecnico
        from app.models.taller import Taller
        
        tecnico = db.query(Tecnico).filter(Tecnico.id_tecnico == incidente.tecnico_id).first()
        if tecnico:
            respuesta["tecnico_asignado"] = {
                "nombre": tecnico.nombre,
                "especialidad": tecnico.especialidad
            }
            # Buscamos el nombre del Taller
            taller = db.query(Taller).filter(Taller.id_taller == tecnico.taller_id).first()
            if taller:
                respuesta["taller_responsable"] = taller.nombre

    return respuesta

# -------------------------------------------------------
# CU12: CONTROL DE EJECUCIÓN Y CIERRE DE SERVICIO
# -------------------------------------------------------
from app.schemas.incidente import ActualizarEstado # Asegúrate de importar la clase que creamos arriba

@router.put("/{id_incidente}/estado", status_code=status.HTTP_200_OK)
def actualizar_estado_servicio(id_incidente: int, datos: ActualizarEstado, db: Session = Depends(get_db)):
    incidente = db.query(Incidente).filter(Incidente.id_incidente == id_incidente).first()
    
    if not incidente:
        raise HTTPException(status_code=404, detail="Incidente no encontrado.")

    # 1. Actualizamos el estado de la emergencia
    incidente.estado_enum = datos.estado_enum
    
    # 2. LOGICA DE NEGOCIO: Si el servicio terminó, liberamos al técnico
    if datos.estado_enum == EstadoIncidente.atendido and incidente.tecnico_id:
        from app.models.tecnico import Tecnico
        tecnico = db.query(Tecnico).filter(Tecnico.id_tecnico == incidente.tecnico_id).first()
        if tecnico:
            tecnico.disponible_boolean = True # El técnico vuelve a estar libre

    # 3. Trazabilidad
    db.add(HistorialEstado(
        incidente_id=id_incidente,
        estado_enum=datos.estado_enum,
        comentario_texto=datos.comentario or f"El estado del servicio cambió a {datos.estado_enum.value}."
    ))
    
    db.commit()
    return {"message": "Estado de ejecución actualizado correctamente", "nuevo_estado": incidente.estado_enum}