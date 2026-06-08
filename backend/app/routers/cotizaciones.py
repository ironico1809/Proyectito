from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime
from typing import List
from app.database import get_db
from app.models.cotizacion import Cotizacion
from app.models.incidente import Incidente, EstadoIncidente
from app.schemas.cotizacion import CotizacionCreate, CotizacionResponse
from app.routers.websocket_incidente import gestor  # Para broadcast en tiempo real
from app.routers.auth import get_current_user
from app.models.usuario import Usuario, TipoRol
from app.utils.bitacora import registrar_evento  # CU21 — bitácora

router = APIRouter(prefix="/cotizaciones", tags=["CU18 - Cotizaciones"])

# ===================================================================
# CU18: TALLER ENVÍA UNA COTIZACIÓN AL INCIDENTE
# ===================================================================
@router.post("/", response_model=CotizacionResponse, status_code=status.HTTP_201_CREATED)
async def crear_cotizacion(
    cotizacion: CotizacionCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Verificar que el incidente existe
    incidente = db.query(Incidente).filter(Incidente.id_incidente == cotizacion.incidente_id).first()
    if not incidente:
        raise HTTPException(status_code=404, detail="Incidente no encontrado.")

    # El taller_id se obtiene buscando el taller del usuario autenticado
    from app.models.taller import Taller
    taller = db.query(Taller).filter(Taller.dueño_id == current_user.id_usuario).first()
    if not taller:
        raise HTTPException(status_code=403, detail="El usuario no tiene un taller asociado.")

    nueva_cotizacion = Cotizacion(
        incidente_id=cotizacion.incidente_id,
        taller_id=taller.id_taller,
        precio_estimado=cotizacion.precio_estimado,
        tiempo_estimado_min=cotizacion.tiempo_estimado_min,
        descripcion=cotizacion.descripcion
    )
    db.add(nueva_cotizacion)

    # CU21 — registrar envío de cotización en bitácora
    registrar_evento(
        db, cotizacion.incidente_id,
        "COTIZACION_ENVIADA",
        f"Taller '{taller.nombre}' envió cotización: {cotizacion.precio_estimado} Bs., {cotizacion.tiempo_estimado_min} min.",
        current_user.id_usuario
    )

    db.commit()
    db.refresh(nueva_cotizacion)

    from app.routers.notificaciones import crear_notificacion_interna
    crear_notificacion_interna(db, incidente.cliente_id, "Nueva Cotización", f"El taller {taller.nombre} ha enviado una cotización de {cotizacion.precio_estimado} Bs.")

    # Notificar al cliente por WebSocket que llegó una nueva cotización
    await gestor.broadcast(cotizacion.incidente_id, {
        "tipo": "nueva_cotizacion",
        "taller": taller.nombre,
        "precio": str(cotizacion.precio_estimado),
        "tiempo_min": cotizacion.tiempo_estimado_min,
        "timestamp": datetime.now().isoformat()
    })

    return nueva_cotizacion

# ===================================================================
# CU18: CLIENTE VE TODAS LAS COTIZACIONES DE SU INCIDENTE
# ===================================================================
@router.get("/{incidente_id}", response_model=List[CotizacionResponse])
async def obtener_cotizaciones(
    incidente_id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    cotizaciones = db.query(Cotizacion).filter(
        Cotizacion.incidente_id == incidente_id
    ).order_by(Cotizacion.fecha_envio.asc()).all()
    incidente = db.query(Incidente).filter(
        Incidente.id_incidente == incidente_id
    ).first()
    if not incidente:
        raise HTTPException(status_code=404, detail="Incidente no encontrado.")

    # Control de acceso eliminado temporalmente por petición del usuario
    return cotizaciones

# ===================================================================
# CU18: CLIENTE ACEPTA UNA COTIZACIÓN
# Cambia el estado del incidente a taller_asignado y notifica por WS
# ===================================================================
@router.put("/{id}/aceptar")
async def aceptar_cotizacion(
    id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    cotizacion = db.query(Cotizacion).filter(Cotizacion.id_cotizacion == id).first()
    if not cotizacion:
        raise HTTPException(status_code=404, detail="Cotización no encontrada.")

    if cotizacion.estado != "pendiente":
        raise HTTPException(status_code=400, detail="Esta cotización ya fue procesada.")

    # 1. Marcar esta cotización como aceptada
    cotizacion.estado = "aceptada"
    cotizacion.fecha_respuesta = datetime.utcnow()

    # 2. Expirar todas las demás cotizaciones del mismo incidente
    db.query(Cotizacion).filter(
        Cotizacion.incidente_id == cotizacion.incidente_id,
        Cotizacion.id_cotizacion != id
    ).update({"estado": "expirada"})

    # 3. Actualizar el incidente: nuevo estado y taller asignado
    incidente = db.query(Incidente).filter(Incidente.id_incidente == cotizacion.incidente_id).first()
    if not incidente:
        raise HTTPException(status_code=404, detail="Incidente no encontrado.")
    incidente.taller_actual_id = cotizacion.taller_id

    # 4. Auto-asignar un técnico disponible del taller aceptado
    from app.models.tecnico import Tecnico
    from app.models.incidente import HistorialEstado
    from app.routers.notificaciones import crear_notificacion_interna

    tecnico = db.query(Tecnico).filter(
        Tecnico.taller_id == cotizacion.taller_id,
        Tecnico.disponible_boolean == True
    ).first()

    if tecnico:
        incidente.tecnico_id = tecnico.id_tecnico
        incidente.estado_enum = EstadoIncidente.en_proceso
        tecnico.disponible_boolean = False

        db.add(HistorialEstado(
            incidente_id=incidente.id_incidente,
            estado_enum=EstadoIncidente.taller_asignado,
            comentario_texto=f"Cotización aceptada. Taller asignado."
        ))
        db.add(HistorialEstado(
            incidente_id=incidente.id_incidente,
            estado_enum=EstadoIncidente.en_proceso,
            comentario_texto=f"Técnico {tecnico.nombre} asignado automáticamente y en camino."
        ))
        crear_notificacion_interna(
            db, incidente.cliente_id,
            "Técnico Asignado",
            f"El mecánico {tecnico.nombre} va en ruta hacia tu ubicación."
        )

        # CU21 — registrar asignación automática en bitácora
        registrar_evento(
            db, incidente.id_incidente,
            "TECNICO_AUTO_ASIGNADO",
            f"Técnico {tecnico.nombre} (ID {tecnico.id_tecnico}) asignado automáticamente tras aceptar cotización.",
            current_user.id_usuario
        )
    else:
        # No hay técnico disponible, dejar en taller_asignado
        incidente.estado_enum = EstadoIncidente.taller_asignado
        db.add(HistorialEstado(
            incidente_id=incidente.id_incidente,
            estado_enum=EstadoIncidente.taller_asignado,
            comentario_texto="Cotización aceptada. Taller asignado. Esperando técnico disponible."
        ))

    # 5. CU21 — registrar cotización aceptada en bitácora
    registrar_evento(
        db, cotizacion.incidente_id,
        "COTIZACION_ACEPTADA",
        f"El cliente aceptó la cotización del taller ID {cotizacion.taller_id}. "
        f"Precio: {cotizacion.precio_estimado} Bs. Tiempo estimado: {cotizacion.tiempo_estimado_min} min.",
        current_user.id_usuario
    )

    db.commit()

    # 6. Broadcast WebSocket — notificar a todos en la sala del incidente
    estado_final = "en_proceso" if tecnico else "taller_asignado"
    mensaje_ws = f"Técnico {tecnico.nombre} asignado y en camino." if tecnico else "Taller asignado. Esperando técnico."
    await gestor.broadcast(incidente.id_incidente, {
        "tipo": "cambio_estado",
        "estado": estado_final,
        "mensaje": mensaje_ws,
        "tecnico_nombre": tecnico.nombre if tecnico else None,
        "taller_id": cotizacion.taller_id,
        "timestamp": datetime.now().isoformat()
    })

    return {"mensaje": f"Cotización aceptada. {'Técnico ' + tecnico.nombre + ' asignado.' if tecnico else 'Taller asignado, esperando técnico.'}"}

# ===================================================================
# CU18: CLIENTE RECHAZA UNA COTIZACIÓN
# ===================================================================
@router.put("/{id}/rechazar")
async def rechazar_cotizacion(
    id: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    cotizacion = db.query(Cotizacion).filter(Cotizacion.id_cotizacion == id).first()
    if not cotizacion:
        raise HTTPException(status_code=404, detail="Cotización no encontrada.")

    if cotizacion.estado != "pendiente":
        raise HTTPException(status_code=400, detail="Esta cotización ya fue procesada.")

    cotizacion.estado = "rechazada"
    cotizacion.fecha_respuesta = datetime.utcnow()

    # CU21 — registrar rechazo en bitácora
    registrar_evento(
        db, cotizacion.incidente_id,
        "COTIZACION_RECHAZADA",
        f"El cliente rechazó la cotización del taller ID {cotizacion.taller_id}.",
        current_user.id_usuario
    )

    db.commit()
    return {"mensaje": "Cotización rechazada."}