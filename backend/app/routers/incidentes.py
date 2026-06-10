import math
import requests
import base64
import json
import os
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload
from pydantic import BaseModel
from app.models.pago import Pago
from app.database import get_db, SessionLocal
from app.models.usuario import Usuario, TipoRol
from app.models.vehiculo import Vehiculo
from app.models.taller import Taller
from app.models.tecnico import Tecnico
from app.models.incidente import Incidente, EvidenciaIA, HistorialEstado, EstadoIncidente, TipoEvidencia, PrioridadIncidente
from app.schemas.incidente import IncidenteCreate, IncidenteOut, AccionSolicitud, AsignarTecnico, ActualizarEstado, PaginatedIncidentes
from app.routers.auth import get_current_user
from app.routers.notificaciones import crear_notificacion_interna
from app.models.taller_rechazo import TallerRechazo
from app.utils.bitacora import registrar_evento  # CU21 — helper de bitácora
from apscheduler.schedulers.background import BackgroundScheduler
from app.models.excepcion import ExcepcionOperativa
from app.models.cotizacion import Cotizacion
from app.routers.websocket_incidente import gestor, gestor_general
import asyncio
from google import genai
from google.genai import types
from pydantic import Field

class AnalisisEmergencia(BaseModel):
    resumen: str = Field(description="Resumen técnico y directo del incidente en un máximo de 8 palabras (ej: 'Neumático delantero pinchado'). No excedas este límite bajo ninguna circunstancia.")
    clasificacion: str = Field(description="Clasificación del tipo de incidente: choque, bateria, llanta, motor, u otros.")
    prioridad: str = Field(description="Nivel de prioridad del incidente: alta, media, o baja.")


router = APIRouter(prefix="/incidentes", tags=["Gestion Inteligente de Incidentes"])

# ===================================================================
# CU8: MOTOR PROFESIONAL "GROQ" BLINDADO (Cero caídas)
# ===================================================================
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")

def transcribir_audio_groq(audio_bytes: bytes):
    """Usa Whisper Large V3 en Groq para transcribir el .m4a del celular al instante."""
    url = "https://api.groq.com/openai/v1/audio/transcriptions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    files = {"file": ("audio.m4a", audio_bytes, "audio/m4a")}
    data = {"model": "whisper-large-v3", "response_format": "json"}
    try:
        res = requests.post(url, headers=headers, files=files, data=data, timeout=10)
        if res.status_code == 200:
            texto = res.json().get("text", "").strip()
            return texto if texto else "Audio inaudible o vacío."
        else:
            print("Error Groq Audio:", res.text)
            return "Audio recibido (No se pudo transcribir)."
    except Exception as e:
        print("Excepción Groq Audio:", e)
        return "Audio recibido. (Fallo de red al transcribir)."

def clasificador_local_seguro(descripcion: str, transcripcion: str):
    """SALVAVIDAS: Si Groq se cae por completo, Python clasifica el texto."""
    texto_total = f"{descripcion} {transcripcion}".lower()
    clasificacion = "otros"
    prioridad = "incierto"
    resumen = "Evaluación técnica requerida."
    if any(p in texto_total for p in ["llan", "pinch", "tire", "goma", "flat", "rueda"]):
        clasificacion, prioridad, resumen = "llanta", "media", "Problema de neumático detectado."
    elif any(p in texto_total for p in ["cho", "acciden", "golp", "crash", "damage"]):
        clasificacion, prioridad, resumen = "choque", "alta", "Colisión vehicular detectada."
    elif any(p in texto_total for p in ["bat", "arran", "encien", "electr", "battery"]):
        clasificacion, prioridad, resumen = "bateria", "media", "Posible descarga de batería."
    elif any(p in texto_total for p in ["mot", "hum", "calien", "radia", "engine"]):
        clasificacion, prioridad, resumen = "motor", "alta", "Falla de motor o sobrecalentamiento."
    return f"[{clasificacion.upper()}] Prioridad {prioridad.upper()}: {resumen}"[:95], prioridad

def analizar_emergencia_gemini(b64_img: str, descripcion: str, transcripcion: str):
    """Usa el SDK oficial de Google GenAI con gemini-3.5-flash."""
    # Si no hay texto ni audio ni imagen, usar clasificador local
    if not b64_img and not descripcion and not transcripcion:
        return clasificador_local_seguro(descripcion, transcripcion)

    try:
        client = genai.Client()
        
        texto_prompt = f"""
        Eres un perito experto en vehículos. Analiza la siguiente emergencia.
        Descripción del cliente: "{descripcion}"
        Lo que el cliente dijo en el audio: "{transcripcion}"
        """
        
        contents = []
        if b64_img:
            try:
                img_bytes = base64.b64decode(b64_img)
                contents.append(types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"))
            except Exception as e:
                print("Error decodificando imagen en analizar_emergencia_gemini:", e)
        
        contents.append(texto_prompt)
        
        response = client.models.generate_content(
            model='gemini-3.5-flash',
            contents=contents,
            config=types.GenerateContentConfig(
                temperature=0.2,
                response_mime_type='application/json',
                response_schema=AnalisisEmergencia,
            ),
        )
        
        dict_ia = json.loads(response.text.strip())
        clasificacion = dict_ia.get("clasificacion", "otros").upper()
        prioridad = dict_ia.get("prioridad", "incierto").lower()
        resumen = dict_ia.get("resumen", "Análisis completado.")
        
        return f"[{clasificacion}] Prioridad {prioridad.upper()}: {resumen}"[:95], prioridad
    except Exception as e:
        print(f"Excepción al usar SDK google-genai: {e}")
        
    return clasificador_local_seguro(descripcion, transcripcion)


# ===================================================================
# ENDPOINT PARA RECIBIR IMÁGENES BASE64 DESDE FLUTTER
# ===================================================================
class ImageUpload(BaseModel):
    image_data: str

@router.post("/subir-imagen")
def subir_imagen(upload: ImageUpload):
    return {"url": f"data:image/jpeg;base64,{upload.image_data}"}

# ===================================================================
# RUTEO INTELIGENTE Y CRON JOB
# ===================================================================
def calcular_distancia(lat1, lon1, lat2, lon2):
    if not all([lat1, lon1, lat2, lon2]): return float('inf')
    R = 6371.0
    dlat = math.radians(float(lat2) - float(lat1))
    dlon = math.radians(float(lon2) - float(lon1))
    a = math.sin(dlat/2)**2 + math.cos(math.radians(float(lat1))) * math.cos(math.radians(float(lat2))) * math.sin(dlon/2)**2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))

def buscar_taller_disponible(db, lat_emergencia, lon_emergencia, incidente_id=None, item_requerido=None, tenant_id=None):
    excluidos_ids = []
    if incidente_id:
        rechazos = db.query(TallerRechazo.taller_id).filter(
            TallerRechazo.incidente_id == incidente_id
        ).all()
        excluidos_ids = [r[0] for r in rechazos]

    query = db.query(Taller)
    if tenant_id is not None:
        query = query.filter(Taller.tenant_id == tenant_id)
    talleres = query.all()
    mejor_taller, dist_min = None, float('inf')

    for t in talleres:
        if t.id_taller in excluidos_ids:
            continue
            
        # Filtro de Inventario (Idea 2)
        if item_requerido and item_requerido in ["bateria", "llanta", "aceite"]:
            from app.models.taller import TallerInventario
            stock = db.query(TallerInventario).filter(
                TallerInventario.taller_id == t.id_taller,
                TallerInventario.item_nombre == item_requerido,
                TallerInventario.cantidad > 0
            ).first()
            if not stock:
                continue # Saltar taller si no tiene stock

        if db.query(Tecnico).filter(
            Tecnico.taller_id == t.id_taller,
            Tecnico.disponible_boolean == True
        ).first():
            d = calcular_distancia(lat_emergencia, lon_emergencia,
                                   t.latitud_decimal, t.longitud_decimal)
            if d < dist_min:
                dist_min, mejor_taller = d, t

    return mejor_taller, dist_min

def robot_reasignacion_automatica():
    """Cron job: reasigna automáticamente incidentes sin respuesta tras 5 minutos."""
    db = SessionLocal()
    try:
        ahora = datetime.now()
        estancados = db.query(Incidente).filter(
            Incidente.estado_enum == EstadoIncidente.pendiente,
            Incidente.fecha_creacion_timestamp <= ahora - timedelta(minutes=5)
        ).all()
        for inc in estancados:
            # 1. Registrar rechazo automático por timeout
            if inc.taller_actual_id:
                db.add(TallerRechazo(
                    incidente_id=inc.id_incidente,
                    taller_id=inc.taller_actual_id,
                    motivo="Timeout: El taller no respondió en 5 minutos."
                ))
                db.flush()

            # 2. Buscar nuevo taller (el taller anterior ya está excluido por TallerRechazo)
            nuevo_taller, dist = buscar_taller_disponible(db, inc.latitud_emergencia, inc.longitud_emergencia, inc.id_incidente, tenant_id=inc.tenant_id)
            
            if nuevo_taller:
                msg = f"Ventana expirada. Reasignado a Taller ID: {nuevo_taller.id_taller}"
                inc.taller_actual_id = nuevo_taller.id_taller
                inc.fecha_creacion_timestamp = ahora
                crear_notificacion_interna(db, nuevo_taller.dueño_id, "🚨 Alerta Reasignada", "Nueva alerta derivada hacia ti.")
                # CU21 — registrar reasignación automática en bitácora
                registrar_evento(db, inc.id_incidente, "REASIGNACION_AUTOMATICA", msg)
                db.add(HistorialEstado(incidente_id=inc.id_incidente, estado_enum=EstadoIncidente.pendiente, comentario_texto=msg))
            else:
                msg = "Ventana expirada. No hay más talleres disponibles. Incidente cancelado."
                inc.taller_actual_id = None
                inc.estado_enum = EstadoIncidente.cancelado
                db.add(HistorialEstado(incidente_id=inc.id_incidente, estado_enum=EstadoIncidente.cancelado, comentario_texto=msg))
                # Notificar al cliente que se canceló
                crear_notificacion_interna(db, inc.cliente_id, "Búsqueda Cancelada", "Ningún taller respondió a tiempo. Intenta generar la emergencia nuevamente.")
            
            db.commit()
    finally:
        db.close()

scheduler = BackgroundScheduler()
scheduler.add_job(
    robot_reasignacion_automatica, 
    'interval', 
    minutes=1, 
    max_instances=3,
    misfire_grace_time=30
)
scheduler.start()

class UbicacionTecnicoUpdate(BaseModel):
    latitud: float
    longitud: float

@router.put("/{id_incidente}/ubicacion-tecnico")
def actualizar_ubicacion_tecnico(
    id_incidente: int,
    datos: UbicacionTecnicoUpdate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """Actualiza la posición GPS del técnico en tiempo real."""
    incidente = db.query(Incidente).filter(Incidente.id_incidente == id_incidente).first()
    if incidente:
        incidente.latitud_tecnico = datos.latitud
        incidente.longitud_tecnico = datos.longitud
        db.commit()
        # Notificar en tiempo real al cliente y taller en la sala del incidente
        background_tasks.add_task(broadcast_async, id_incidente, {
            "tipo": "ubicacion_tecnico",
            "latitud": datos.latitud,
            "longitud": datos.longitud,
            "timestamp": datetime.now().isoformat()
        })
    return {"status": "ok"}

def broadcast_async(incidente_id, payload):
    asyncio.run(gestor.broadcast(incidente_id, payload))

def broadcast_general_async(tenant_id, payload):
    """Broadcast a message to all connected web portals (sala general)."""
    asyncio.run(gestor_general.broadcast(tenant_id, payload))

# ===================================================================
# CU7: REGISTRAR EMERGENCIA — acepta audio, imagen o texto por separado
# ===================================================================
@router.post("/", response_model=IncidenteOut, status_code=status.HTTP_201_CREATED)
def registrar_emergencia(
    datos: IncidenteCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Verificar que el vehículo pertenece al cliente
    vehiculo = db.query(Vehiculo).filter(Vehiculo.id_vehiculo == datos.vehiculo_id).first()
    if not vehiculo:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado.")

    # Validar que venga al menos un canal de evidencia (texto, foto o audio)
    texto_cliente = datos.descripcion_texto or ""
    tiene_audio  = any("audio"  in str(ev.tipo_enum) for ev in datos.evidencias)
    tiene_imagen = any("imagen" in str(ev.tipo_enum) for ev in datos.evidencias)
    tiene_texto  = bool(texto_cliente.strip())

    if not tiene_texto and not tiene_audio and not tiene_imagen:
        raise HTTPException(status_code=400, detail="Debes enviar al menos una descripción, foto o audio.")

    # Procesar cada canal de evidencia de forma INDEPENDIENTE
    b64_img, audio_bytes, transcripcion = None, None, ""

    for ev in datos.evidencias:
        tipo_str = str(ev.tipo_enum.value) if hasattr(ev.tipo_enum, 'value') else str(ev.tipo_enum)
        url = ev.url_recurso

        if "imagen" in tipo_str:
            if url.startswith("data:image"):
                try: b64_img = url.split(",")[1]
                except: b64_img = None
            else:
                b64_img = url

        elif "audio" in tipo_str:
            if url.startswith("data:audio"):
                try: audio_bytes = base64.b64decode(url.split(",")[1])
                except: audio_bytes = None
            else:
                try: audio_bytes = base64.b64decode(url)
                except: audio_bytes = None

    # Transcribir audio solo si vino audio
    if audio_bytes:
        transcripcion = transcribir_audio_groq(audio_bytes)

    # La IA analiza con lo que tenga disponible
    texto_resumen_seguro, prioridad_ia = analizar_emergencia_gemini(b64_img, texto_cliente, transcripcion)
    clasificacion_pura = texto_resumen_seguro.split(']')[0].replace('[', '').strip().lower()

    # Buscar el taller más cercano disponible considerando Inventario
    taller, dist = buscar_taller_disponible(db, datos.latitud_emergencia, datos.longitud_emergencia, item_requerido=clasificacion_pura, tenant_id=current_user.tenant_id)

    # Verificar uuid_offline para evitar duplicados de sincronización offline
    if datos.uuid_offline:
        ya_existe = db.query(Incidente).filter(Incidente.uuid_offline == datos.uuid_offline).first()
        if ya_existe:
            # Si ya existe devolver el mismo sin duplicar
            return ya_existe

    nuevo_incidente = Incidente(
        cliente_id=current_user.id_usuario,
        vehiculo_id=datos.vehiculo_id,
        taller_actual_id=taller.id_taller if taller else None,
        latitud_emergencia=datos.latitud_emergencia,
        longitud_emergencia=datos.longitud_emergencia,
        descripcion_texto=datos.descripcion_texto,
        latitud_tecnico=float(taller.latitud_decimal) if (taller and taller.latitud_decimal is not None) else None,
        longitud_tecnico=float(taller.longitud_decimal) if (taller and taller.longitud_decimal is not None) else None,
        uuid_offline=datos.uuid_offline,  # CU19 — sincronización offline
        tenant_id=current_user.tenant_id
    )
    db.add(nuevo_incidente)
    db.flush()

    try:
        nuevo_incidente.prioridad_enum = PrioridadIncidente(prioridad_ia)
    except ValueError:
        nuevo_incidente.prioridad_enum = PrioridadIncidente.incierto

    # Guardar evidencias en BD
    for ev in datos.evidencias:
        tipo_raw = ev.tipo_enum
        tipo_str = str(tipo_raw.value) if hasattr(tipo_raw, 'value') else str(tipo_raw)
        transcripcion_guardar = transcripcion if "audio" in tipo_str and transcripcion else None
        db.add(EvidenciaIA(
            incidente_id=nuevo_incidente.id_incidente,
            tipo_enum=tipo_raw,
            url_recurso=ev.url_recurso,
            clasificacion_ia_texto=texto_resumen_seguro,
            nivel_confianza=0.98,
            transcripcion_audio_texto=transcripcion_guardar
        ))

    # Guardar historial y notificaciones
    comentario = f"Alerta enviada a Taller ID: {taller.id_taller} ({dist:.2f}km)" if taller else "Buscando taller..."
    db.add(HistorialEstado(incidente_id=nuevo_incidente.id_incidente, estado_enum=EstadoIncidente.pendiente, comentario_texto=comentario))
    crear_notificacion_interna(db, current_user.id_usuario, "Emergencia Registrada", "La IA procesó tu caso.")
    if taller:
        crear_notificacion_interna(db, taller.dueño_id, "🚨 Nueva Alerta", f"Vehículo a {dist:.2f}km.")

    # CU21 — registrar creación en bitácora
    registrar_evento(
        db, nuevo_incidente.id_incidente,
        "CREACION",
        f"Emergencia registrada. Prioridad IA: {prioridad_ia}. Taller asignado: {taller.id_taller if taller else 'Ninguno'}",
        current_user.id_usuario
    )

    db.commit()
    db.refresh(nuevo_incidente)

    # Notificar al portal web en tiempo real sobre la nueva emergencia
    background_tasks.add_task(broadcast_general_async, nuevo_incidente.tenant_id, {
        "tipo": "nuevo_incidente",
        "id_incidente": nuevo_incidente.id_incidente,
        "estado": nuevo_incidente.estado_enum.value if hasattr(nuevo_incidente.estado_enum, 'value') else str(nuevo_incidente.estado_enum),
        "prioridad": nuevo_incidente.prioridad_enum.value if hasattr(nuevo_incidente.prioridad_enum, 'value') else str(nuevo_incidente.prioridad_enum),
        "descripcion": nuevo_incidente.descripcion_texto or "",
        "latitud": float(nuevo_incidente.latitud_emergencia) if nuevo_incidente.latitud_emergencia else None,
        "longitud": float(nuevo_incidente.longitud_emergencia) if nuevo_incidente.longitud_emergencia else None,
        "taller_id": nuevo_incidente.taller_actual_id,
        "timestamp": datetime.now().isoformat()
    })

    # ===================================================================
    # AUTOGENERACIÓN DE COTIZACIONES BASADA EN IA
    # ===================================================================
    clasificacion_pura = texto_resumen_seguro.split(']')[0].replace('[', '').strip().lower()
    talleres_cercanos = db.query(Taller).filter(Taller.tenant_id == current_user.tenant_id).all()
    # Ordenar talleres por distancia
    lista_talleres = []
    for t in talleres_cercanos:
        d = calcular_distancia(datos.latitud_emergencia, datos.longitud_emergencia, t.latitud_decimal, t.longitud_decimal)
        lista_talleres.append((t, d))
    lista_talleres.sort(key=lambda x: x[1])

    # Tomar los 2 talleres más cercanos
    top_2_talleres = [x[0] for x in lista_talleres[:2]]

    precio = 0.0
    desc_coti = ""
    if clasificacion_pura == "llanta":
        precio = 40.0
        desc_coti = "Gomería express. Solución de llanta en el lugar. Precio automático."
    elif clasificacion_pura == "bateria":
        precio = 50.0
        desc_coti = "Servicio Estándar de Batería. Precio automático."
    elif clasificacion_pura in ["motor", "choque"]:
        precio = 30.0
        desc_coti = "⚠️ Problema complejo. El precio final variará tras evaluación. Costo solo por diagnóstico/visita."
    else:
        precio = 60.0
        desc_coti = "Revisión técnica general requerida en el lugar."

    # Insertar cotizaciones
    nuevas_coti = []
    for i, t in enumerate(top_2_talleres):
        tiempo_est = 15 + (i * 10)  # El primero llega en 15, el segundo en 25
        coti = Cotizacion(
            incidente_id=nuevo_incidente.id_incidente,
            taller_id=t.id_taller,
            precio_estimado=precio + (i * 10), # Variar un poco el precio
            tiempo_estimado_min=tiempo_est,
            descripcion=desc_coti,
            estado="pendiente"
        )
        db.add(coti)
        nuevas_coti.append(coti)

    db.commit()

    # Si hay WebSocket activo, enviarlas
    if nuevas_coti:
        for c in nuevas_coti:
            payload = {
                "tipo": "nueva_cotizacion",
                "cotizacion_id": c.id_cotizacion,
                "taller_id": c.taller_id,
                "taller_nombre": c.taller.nombre if c.taller else f"Taller #{c.taller_id}",
                "precio": float(c.precio_estimado),
                "tiempo_min": c.tiempo_estimado_min,
                "descripcion": c.descripcion,
                "timestamp": datetime.now().isoformat()
            }
            background_tasks.add_task(broadcast_async, nuevo_incidente.id_incidente, payload)

    return nuevo_incidente

# ===================================================================
# CU10: LISTAR EMERGENCIAS PENDIENTES (para el taller en Angular)
# ===================================================================
@router.get("/pendientes", response_model=List[IncidenteOut])
def listar_solicitudes_pendientes(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Buscar el taller del usuario autenticado
    taller = db.query(Taller).filter(
        Taller.dueño_id == current_user.id_usuario
    ).first()

    if not taller:
        # Acceso total temporal
        query = db.query(Incidente).filter(
            Incidente.estado_enum == EstadoIncidente.pendiente
        )
        if current_user.tenant_id is not None:
            query = query.filter(Incidente.tenant_id == current_user.tenant_id)
        return query.all()

    # Obtener IDs de incidentes que este taller ya rechazó
    rechazados = db.query(TallerRechazo.incidente_id).filter(
        TallerRechazo.taller_id == taller.id_taller
    ).all()
    ids_rechazados = [r[0] for r in rechazados]

    # Solo ver el incidente asignado a este taller y que no haya rechazado
    return db.query(Incidente).filter(
        Incidente.estado_enum == EstadoIncidente.pendiente,
        Incidente.taller_actual_id == taller.id_taller,
        Incidente.id_incidente.notin_(ids_rechazados)
    ).all()
# ===================================================================
# CU10: ACEPTAR O RECHAZAR SOLICITUD (taller responde)
# ===================================================================
@router.post("/{id_incidente}/accion")
def responder_solicitud(
    id_incidente: int,
    datos: AccionSolicitud,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    incidente = db.query(Incidente).filter(Incidente.id_incidente == id_incidente).first()
    if not incidente or incidente.estado_enum != EstadoIncidente.pendiente:
        raise HTTPException(status_code=400, detail="El incidente ya no está disponible.")

    if datos.accion == "aceptar":
        incidente.estado_enum = EstadoIncidente.en_proceso
        db.add(HistorialEstado(
            incidente_id=id_incidente,
            estado_enum=EstadoIncidente.en_proceso,
            comentario_texto="Solicitud aceptada por el Taller."
        ))
        crear_notificacion_interna(db, incidente.cliente_id, "¡Auxilio en camino!", "Tu solicitud ha sido aceptada.")
        # CU21 — registrar aceptación en bitácora
        registrar_evento(
            db, id_incidente,
            "TALLER_ACEPTO",
            f"El taller ID {incidente.taller_actual_id} aceptó la solicitud.",
            current_user.id_usuario
        )

    elif datos.accion == "rechazar":
        db.add(TallerRechazo(
            incidente_id=id_incidente,
            taller_id=incidente.taller_actual_id,
            motivo=datos.comentario or "Sin motivo."
        ))
        db.flush()
        crear_notificacion_interna(db, incidente.cliente_id, "Taller Rechazado", "El taller actual rechazó la solicitud. Buscando alternativas...")
        nuevo_taller, dist = buscar_taller_disponible(db, incidente.latitud_emergencia, incidente.longitud_emergencia, id_incidente)
        if nuevo_taller:
            incidente.taller_actual_id = nuevo_taller.id_taller
            incidente.fecha_creacion_timestamp = datetime.now()
            db.add(HistorialEstado(
                incidente_id=id_incidente,
                estado_enum=EstadoIncidente.pendiente,
                comentario_texto=f"Reasignado a Taller ID: {nuevo_taller.id_taller}"
            ))
            crear_notificacion_interna(db, nuevo_taller.dueño_id, "🚨 Emergencia Derivada", f"Un incidente a {dist:.2f}km derivado a tu taller.")
        else:
            incidente.taller_actual_id = None
            db.add(HistorialEstado(
                incidente_id=id_incidente,
                estado_enum=EstadoIncidente.pendiente,
                comentario_texto="Rechazado. No hay más talleres disponibles en la zona."
            ))
        # CU21 — registrar rechazo en bitácora
        registrar_evento(
            db, id_incidente,
            "TALLER_RECHAZO",
            datos.comentario or "El taller rechazó la solicitud.",
            current_user.id_usuario
        )

    db.commit()
    return {"status": "ok"}

# ===================================================================
# CU11: ASIGNAR TÉCNICO AL INCIDENTE
# ===================================================================
@router.post("/{id_incidente}/asignar")
def asignar_tecnico(
    id_incidente: int,
    datos: AsignarTecnico,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Verificar que el incidente existe antes de operar
    incidente = db.query(Incidente).filter(Incidente.id_incidente == id_incidente).first()
    if not incidente:
        raise HTTPException(status_code=404, detail="Incidente no encontrado.")

    tecnico = db.query(Tecnico).filter(Tecnico.id_tecnico == datos.tecnico_id).first()
    if not tecnico or not tecnico.disponible_boolean:
        raise HTTPException(status_code=400, detail="El técnico no está disponible.")

    incidente.tecnico_id = datos.tecnico_id
    tecnico.disponible_boolean = False
    db.add(HistorialEstado(
        incidente_id=id_incidente,
        estado_enum=EstadoIncidente.en_proceso,
        comentario_texto=f"Técnico {tecnico.nombre} despachado hacia el lugar."
    ))
    crear_notificacion_interna(db, incidente.cliente_id, "Técnico Asignado", f"El mecánico {tecnico.nombre} va en ruta.")
    # CU21 — registrar asignación de técnico en bitácora
    registrar_evento(
        db, id_incidente,
        "TECNICO_ASIGNADO",
        f"Técnico {tecnico.nombre} (ID {tecnico.id_tecnico}) asignado al incidente.",
        current_user.id_usuario
    )
    # Inicializar ubicación del técnico con las coordenadas del taller
    if incidente.taller_actual_id:
        taller = db.query(Taller).filter(Taller.id_taller == incidente.taller_actual_id).first()
        if taller and taller.latitud_decimal is not None and taller.longitud_decimal is not None:
            incidente.latitud_tecnico = float(taller.latitud_decimal)
            incidente.longitud_tecnico = float(taller.longitud_decimal)

    db.commit()
    # Notificar al cliente y portal via WebSocket
    background_tasks.add_task(broadcast_async, id_incidente, {
        "tipo": "cambio_estado",
        "estado": "en_proceso",
        "mensaje": f"Técnico {tecnico.nombre} despachado hacia el lugar.",
        "tecnico_nombre": tecnico.nombre,
        "timestamp": datetime.now().isoformat()
    })
    if incidente.latitud_tecnico is not None and incidente.longitud_tecnico is not None:
        background_tasks.add_task(broadcast_async, id_incidente, {
            "tipo": "ubicacion_tecnico",
            "latitud": incidente.latitud_tecnico,
            "longitud": incidente.longitud_tecnico,
            "timestamp": datetime.now().isoformat()
        })
    return {"message": "Técnico asignado exitosamente."}

# ===================================================================
# CU12: LISTAR INCIDENTES EN PROCESO (para el técnico en Flutter)
# ===================================================================
@router.get("/en-proceso", response_model=List[IncidenteOut])
def listar_solicitudes_en_proceso(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    query = db.query(Incidente).filter(Incidente.estado_enum == EstadoIncidente.en_proceso)
    if current_user.tenant_id is not None:
        query = query.filter(Incidente.tenant_id == current_user.tenant_id)
    return query.all()

# ===================================================================
# CU12: ACTUALIZAR ESTADO DEL SERVICIO (técnico finaliza o avanza)
# ===================================================================
@router.put("/{id_incidente}/estado", status_code=status.HTTP_200_OK)
def actualizar_estado_servicio(
    id_incidente: int,
    datos: ActualizarEstado,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    incidente = db.query(Incidente).filter(Incidente.id_incidente == id_incidente).first()
    if not incidente:
        raise HTTPException(status_code=404, detail="Incidente no encontrado.")

    incidente.estado_enum = datos.estado_enum

    # Si el servicio fue finalizado: liberar técnico y guardar costo
    if datos.estado_enum in [EstadoIncidente.atendido, EstadoIncidente.finalizado]:
        if incidente.tecnico_id:
            tecnico = db.query(Tecnico).filter(Tecnico.id_tecnico == incidente.tecnico_id).first()
            if tecnico:
                tecnico.disponible_boolean = True
        if datos.costo_final is not None:
            incidente.costo_final_decimal = datos.costo_final

    db.add(HistorialEstado(
        incidente_id=id_incidente,
        estado_enum=datos.estado_enum,
        comentario_texto=datos.comentario or f"Servicio actualizado a {datos.estado_enum.value}."
    ))
    crear_notificacion_interna(
        db, incidente.cliente_id,
        "Actualización de Servicio",
        f"El estado de tu emergencia ahora es: {datos.estado_enum.value.upper()}"
    )
    # CU21 — registrar cambio de estado en bitácora
    registrar_evento(
        db, id_incidente,
        "CAMBIO_ESTADO",
        f"Estado actualizado a '{datos.estado_enum.value}'. {datos.comentario or ''}".strip(),
        current_user.id_usuario
    )

    db.commit()
    # Broadcast estado nuevo a WebSocket sala del incidente
    estado_val = datos.estado_enum.value if hasattr(datos.estado_enum, 'value') else str(datos.estado_enum)
    background_tasks.add_task(broadcast_async, id_incidente, {
        "tipo": "cambio_estado",
        "estado": estado_val,
        "mensaje": datos.comentario or f"Estado actualizado a {estado_val}.",
        "timestamp": datetime.now().isoformat()
    })
    return {"message": "Estado actualizado correctamente", "nuevo_estado": incidente.estado_enum}

# ===================================================================
# CU20: REGISTRAR EXCEPCIÓN OPERATIVA
# Maneja cancelaciones, llegada del seguro y casos mixtos
# ===================================================================
class ExcepcionCreate(BaseModel):
    tipo_excepcion: str
    # Valores válidos:
    # "cancelacion_cliente"  → cliente cancela antes de que llegue el taller
    # "llego_seguro_primero" → el seguro llegó antes que el taller
    # "llegaron_ambos"       → llegaron taller y seguro; taller recibe compensación
    motivo: Optional[str] = None
    compensacion_taller: Optional[float] = 0.00

@router.post("/{id_incidente}/excepcion")
def registrar_excepcion(
    id_incidente: int,
    datos: ExcepcionCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Verificar que el incidente existe y está activo
    incidente = db.query(Incidente).filter(Incidente.id_incidente == id_incidente).first()
    if not incidente:
        raise HTTPException(status_code=404, detail="Incidente no encontrado.")

    # Verificar que el incidente no esté ya cancelado o finalizado
    estados_bloqueados = [EstadoIncidente.cancelado, EstadoIncidente.finalizado, EstadoIncidente.atendido]
    if incidente.estado_enum in estados_bloqueados:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede registrar una excepción en un incidente con estado '{incidente.estado_enum.value}'. Solo se puede cancelar si está activo."
        )

    # Verificar tipo de excepción válido
    tipos_validos = ["cancelacion_cliente", "llego_seguro_primero", "llegaron_ambos", "cancelacion_tecnico"]
    if datos.tipo_excepcion not in tipos_validos:
        raise HTTPException(status_code=400, detail=f"Tipo inválido. Usa: {tipos_validos}")
    
    # Insertar en excepciones_operativas
    nueva_excepcion = ExcepcionOperativa(
        incidente_id=id_incidente,
        tipo_excepcion=datos.tipo_excepcion,
        motivo=datos.motivo or "",
        compensacion_taller=datos.compensacion_taller or 0.00
    )
    db.add(nueva_excepcion)
    
    # Cancelar el incidente en todos los casos
    incidente.estado_enum = EstadoIncidente.cancelado
    
    # Liberar al técnico si estaba asignado
    if incidente.tecnico_id:
        tecnico = db.query(Tecnico).filter(
            Tecnico.id_tecnico == incidente.tecnico_id
        ).first()
        if tecnico:
            tecnico.disponible_boolean = True
            
    # Guardar historial
    db.add(HistorialEstado(
        incidente_id=id_incidente,
        estado_enum=EstadoIncidente.cancelado,
        comentario_texto=f"Excepción: {datos.tipo_excepcion}. {datos.motivo or ''}"
    ))
    
    # ============================================================
    # COMPENSACIÓN AL TALLER — solo si llegaron ambos o seguro
    # Se genera un pago especial con estado "compensacion"
    # La BD no acepta montos de 0, así que solo se crea si hay monto real
    # ============================================================
    if datos.tipo_excepcion in ["llegaron_ambos", "llego_seguro_primero"]:
        monto_compensacion = datos.compensacion_taller or 0.00
        if monto_compensacion > 0 and incidente.taller_actual_id:
            from app.models.pago import Pago, MetodoPago
            taller = db.query(Taller).filter(
                Taller.id_taller == incidente.taller_actual_id
            ).first()
            # Verificar que no exista ya un pago para este incidente
            pago_existente = db.query(Pago).filter(
                Pago.incidente_id == id_incidente
            ).first()
            if taller and not pago_existente:
                pago_compensacion = Pago(
                    incidente_id=id_incidente,
                    dueño_taller_id=taller.dueño_id,
                    monto_total_decimal=monto_compensacion,
                    metodo_enum=MetodoPago.transferencia,  # compensación interna
                    estado_pago_enum="compensacion"        # estado especial, distinto de "completado"
                )
                db.add(pago_compensacion)
                crear_notificacion_interna(
                    db, taller.dueño_id,
                    "💰 Compensación por Desplazamiento",
                    f"Recibiste {monto_compensacion} Bs. por el incidente #{id_incidente}."
                )
            # CU21 — registrar compensación en bitácora
            registrar_evento(
                db, id_incidente,
                "COMPENSACION_TALLER",
                f"Compensación de {monto_compensacion} Bs. generada para taller ID {incidente.taller_actual_id}.",
                current_user.id_usuario
            )
        else:
            # Llegaron ambos pero no se indicó monto — notificar igualmente
            if incidente.taller_actual_id:
                taller = db.query(Taller).filter(
                    Taller.id_taller == incidente.taller_actual_id
                ).first()
                if taller:
                    crear_notificacion_interna(
                        db, taller.dueño_id,
                        "ℹ️ Caso Cerrado",
                        f"El incidente #{id_incidente} fue cerrado. "
                        f"Motivo: {datos.tipo_excepcion}. Sin compensación registrada."
                    )
                    
    # Notificar al cliente según el tipo
    mensajes_cliente = {
        "cancelacion_cliente":  "Tu solicitud fue cancelada correctamente.",
        "llego_seguro_primero": "El caso fue cerrado porque llegó tu seguro primero.",
        "llegaron_ambos":       "El caso fue cerrado. El taller recibirá compensación por desplazamiento."
    }
    crear_notificacion_interna(
        db, incidente.cliente_id,
        "Servicio Cancelado",
        mensajes_cliente.get(datos.tipo_excepcion, "El servicio fue cancelado.")
    )
    
    # CU21 — registrar excepción en bitácora
    registrar_evento(
        db, id_incidente,
        "EXCEPCION",
        f"Tipo: {datos.tipo_excepcion}. Motivo: {datos.motivo or 'Sin motivo'}. "
        f"Compensación: {datos.compensacion_taller or 0} Bs.",
        current_user.id_usuario
    )
    
    db.commit()
    
    return {
        "status": "ok",
        "mensaje": "Excepción registrada. Incidente cancelado.",
        "tipo": datos.tipo_excepcion,
        "compensacion_generada": (
            datos.compensacion_taller > 0
            if datos.tipo_excepcion in ["llegaron_ambos", "llego_seguro_primero"]
            else False
        )
    }

# ===================================================================
# CU9: MONITOREO EN TIEMPO REAL DEL AUXILIO
# ===================================================================
@router.get("/{id_incidente}/monitoreo", tags=["CU9 - Monitoreo de Auxilio"])
def monitorear_auxilio(
    id_incidente: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    incidente = db.query(Incidente).filter(Incidente.id_incidente == id_incidente).first()
    if not incidente:
        raise HTTPException(status_code=404, detail="Incidente no encontrado")

    respuesta = {
        "id_incidente": incidente.id_incidente,
        "estado_actual": incidente.estado_enum.value,
        "prioridad": incidente.prioridad_enum.value,
        "latitud_tecnico": float(incidente.latitud_tecnico) if incidente.latitud_tecnico else None,
        "longitud_tecnico": float(incidente.longitud_tecnico) if incidente.longitud_tecnico else None,
        "costo_final_decimal": float(incidente.costo_final_decimal) if incidente.costo_final_decimal else 0.0,
        "tecnico_asignado": None,
        "taller_responsable": None
    }

    if incidente.tecnico_id:
        tecnico = db.query(Tecnico).filter(Tecnico.id_tecnico == incidente.tecnico_id).first()
        if tecnico:
            respuesta["tecnico_asignado"] = {"nombre": tecnico.nombre, "especialidad": tecnico.especialidad}
            taller = db.query(Taller).filter(Taller.id_taller == tecnico.taller_id).first()
            if taller:
                respuesta["taller_responsable"] = taller.nombre

    return respuesta

# ===================================================================
# CU9: RECUPERAR EMERGENCIA ACTIVA DEL CLIENTE TRAS CERRAR SESIÓN
# ===================================================================
@router.get("/cliente/activo", tags=["CU9 - Monitoreo de Auxilio"])
def obtener_emergencia_activa(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    incidente = db.query(Incidente).filter(
        Incidente.cliente_id == current_user.id_usuario,
        Incidente.estado_enum != EstadoIncidente.cancelado
    ).order_by(Incidente.id_incidente.desc()).first()

    if incidente:
        # Si ya fue atendido y tiene pago, el ciclo está cerrado
        if incidente.estado_enum in [EstadoIncidente.atendido, EstadoIncidente.finalizado]:
            pago_existente = db.query(Pago).filter(Pago.incidente_id == incidente.id_incidente).first()
            if pago_existente:
                return {"id_incidente": None}
        return {"id_incidente": incidente.id_incidente}

    return {"id_incidente": None}

@router.get("/tecnico/activo")
def obtener_incidente_activo_tecnico(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    tecnico = db.query(Tecnico).filter(Tecnico.usuario_id == current_user.id_usuario).first()
    if not tecnico:
        return {"id_incidente": None}
    
    incidente = db.query(Incidente).filter(
        Incidente.tecnico_id == tecnico.id_tecnico,
        Incidente.estado_enum.notin_([EstadoIncidente.finalizado, EstadoIncidente.cancelado, EstadoIncidente.atendido])
    ).first()
    return {"id_incidente": incidente.id_incidente if incidente else None}

# ===================================================================
# CU12: HISTORIAL DE SERVICIOS DEL TÉCNICO (solo atendidos)
# ===================================================================
@router.get("/historial/tecnico/{id_tecnico}", tags=["CU12 - Técnico de Auxilio"])
def obtener_historial_tecnico(
    id_tecnico: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    tecnico = db.query(Tecnico).filter(Tecnico.usuario_id == current_user.id_usuario).first()
    if not tecnico:
        return []  # Usuario no es técnico — devolver vacío sin crashear

    # Solo mostrar incidentes finalizados o atendidos
    incidentes = db.query(Incidente).filter(
        Incidente.tecnico_id == tecnico.id_tecnico,
        Incidente.estado_enum.in_([EstadoIncidente.atendido, EstadoIncidente.finalizado])
    ).order_by(Incidente.fecha_creacion_timestamp.desc()).all()

    resultado = []
    for inc in incidentes:
        cliente  = db.query(Usuario).filter(Usuario.id_usuario == inc.cliente_id).first()
        vehiculo = db.query(Vehiculo).filter(Vehiculo.id_vehiculo == inc.vehiculo_id).first()
        resultado.append({
            "id_incidente":            inc.id_incidente,
            "fecha_creacion_timestamp": inc.fecha_creacion_timestamp,
            "estado_enum":             inc.estado_enum.value if hasattr(inc.estado_enum, 'value') else str(inc.estado_enum),
            "cliente_nombre":          cliente.nombre if cliente else "Cliente Anónimo",
            "vehiculo_modelo":         f"{vehiculo.marca} {vehiculo.modelo}" if vehiculo else "Sin registrar"
        })
    return resultado


# ===================================================================
# CU12: HISTORIAL DE SERVICIOS DEL CLIENTE
# ===================================================================
@router.get("/historial/cliente", response_model=List[IncidenteOut], tags=["CU9 - Monitoreo de Auxilio"])
def obtener_historial_cliente(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    incidentes = db.query(Incidente).filter(
        Incidente.cliente_id == current_user.id_usuario
    ).order_by(Incidente.fecha_creacion_timestamp.desc()).all()
    
    # Truncar las cadenas base64 pesadas de las evidencias en el listado de historial
    # para evitar que la petición de red exceda el tiempo límite (timeout)
    for inc in incidentes:
        for ev in inc.evidencias:
            if ev.url_recurso and len(ev.url_recurso) > 1000:
                ev.url_recurso = ev.url_recurso[:200] + "... [TRUNCATED_BASE64]"
                
    return incidentes


# ===================================================================
# OBTENER TODOS LOS INCIDENTES (para el portal)
# ===================================================================
@router.get("/todos", response_model=PaginatedIncidentes, tags=["CU9 - Monitoreo de Auxilio"])
def obtener_todos_los_incidentes(
    page: int = 1,
    limit: int = 10,
    estado: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    query = db.query(Incidente)
    if current_user.tenant_id is not None:
        query = query.filter(Incidente.tenant_id == current_user.tenant_id)

    # Filtrado por Roles (SaaS y nivel de acceso)
    if current_user.rol == "taller":
        taller = db.query(Taller).filter(Taller.dueño_id == current_user.id_usuario).first()
        if taller:
            query = query.filter(
                or_(
                    Incidente.taller_actual_id == taller.id_taller,
                    Incidente.estado_enum.in_([EstadoIncidente.pendiente, EstadoIncidente.buscando_taller])
                )
            )
        else:
            query = query.filter(Incidente.estado_enum.in_([EstadoIncidente.pendiente, EstadoIncidente.buscando_taller]))
            
    elif current_user.rol == "tecnico":
        tecnico = db.query(Tecnico).filter(Tecnico.usuario_id == current_user.id_usuario).first()
        if tecnico:
            query = query.filter(
                or_(
                    Incidente.tecnico_id == tecnico.id_tecnico,
                    Incidente.estado_enum.in_([EstadoIncidente.pendiente, EstadoIncidente.buscando_taller])
                )
            )
        else:
            query = query.filter(Incidente.estado_enum.in_([EstadoIncidente.pendiente, EstadoIncidente.buscando_taller]))
    
    # Eager loading
    query = query.options(
        joinedload(Incidente.cliente),
        joinedload(Incidente.vehiculo),
        joinedload(Incidente.taller_actual),
        joinedload(Incidente.tecnico)
    )

    # Filter by state if specified
    if estado and estado != "todas":
        if estado == "pendientes":
            query = query.filter(Incidente.estado_enum == EstadoIncidente.pendiente)
        elif estado == "en_proceso":
            query = query.filter(Incidente.estado_enum.in_([
                EstadoIncidente.en_proceso,
                EstadoIncidente.buscando_taller,
                EstadoIncidente.taller_asignado,
                EstadoIncidente.en_camino,
                EstadoIncidente.en_atencion
            ]))
        elif estado == "finalizados":
            query = query.filter(Incidente.estado_enum.in_([
                EstadoIncidente.finalizado,
                EstadoIncidente.atendido
            ]))
        elif estado == "cancelados":
            query = query.filter(Incidente.estado_enum == EstadoIncidente.cancelado)

    # Filter by search string
    if search and search.strip():
        search_term = f"%{search.strip()}%"
        conditions = [
            Incidente.descripcion_texto.ilike(search_term),
            Usuario.nombre.ilike(search_term),
            Vehiculo.placa.ilike(search_term),
            Taller.nombre.ilike(search_term),
            Tecnico.nombre.ilike(search_term)
        ]
        try:
            # Match numeric search as id_incidente or client/vehicle IDs
            search_id = int(search.strip())
            conditions.append(Incidente.id_incidente == search_id)
            conditions.append(Incidente.cliente_id == search_id)
            conditions.append(Incidente.vehiculo_id == search_id)
        except ValueError:
            pass
        
        # We need to outer join related tables for this filter
        query = query.outerjoin(Usuario, Incidente.cliente_id == Usuario.id_usuario)\
                     .outerjoin(Vehiculo, Incidente.vehiculo_id == Vehiculo.id_vehiculo)\
                     .outerjoin(Taller, Incidente.taller_actual_id == Taller.id_taller)\
                     .outerjoin(Tecnico, Incidente.tecnico_id == Tecnico.id_tecnico)\
                     .filter(or_(*conditions))

    # Get total count before pagination
    total = query.count()
    
    # Order and apply pagination
    items = query.order_by(Incidente.fecha_creacion_timestamp.desc())\
                 .offset((page - 1) * limit)\
                 .limit(limit)\
                 .all()
                 
    pages = math.ceil(total / limit) if limit > 0 else 1
    
    return {
        "items": items,
        "total": total,
        "page": page,
        "pages": pages
    }

# -------------------------------------------------------
# PATCH /incidentes/{id}/cancelar
# El cliente cancela manualmente el incidente
# -------------------------------------------------------
@router.patch("/{id_incidente}/cancelar", response_model=IncidenteOut)
async def cancelar_incidente(
    id_incidente: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    inc = db.query(Incidente).filter(Incidente.id_incidente == id_incidente).first()
    if not inc:
        raise HTTPException(status_code=404, detail="Incidente no encontrado")
        
    if inc.cliente_id != current_user.id_usuario:
        raise HTTPException(status_code=403, detail="No autorizado para cancelar este incidente")

    if inc.estado_enum in [EstadoIncidente.cancelado, EstadoIncidente.finalizado]:
        raise HTTPException(status_code=400, detail="El incidente ya no se puede cancelar en este estado")

    estado_anterior = inc.estado_enum.value
    taller_id = inc.taller_actual_id

    inc.estado_enum = EstadoIncidente.cancelado
    msg = f"El cliente canceló la emergencia manualmente (estaba en {estado_anterior})."
    
    db.add(HistorialEstado(incidente_id=inc.id_incidente, estado_enum=EstadoIncidente.cancelado, comentario_texto=msg))
    registrar_evento(db, inc.id_incidente, "CANCELADO_POR_CLIENTE", msg)
    
    # Notificar al taller si había uno asignado (pero solo si estaba pendiente de su respuesta)
    if taller_id and estado_anterior in ["pendiente", "cotizando"]:
        taller = db.query(Taller).filter(Taller.id_taller == taller_id).first()
        if taller:
            crear_notificacion_interna(
                db, taller.dueño_id, 
                "Emergencia Cancelada", 
                "El cliente ha cancelado la solicitud de emergencia."
            )
            
    db.commit()
    db.refresh(inc)

    # Broadcast via WebSocket
    await gestor.broadcast(id_incidente, {
        "tipo": "cambio_estado",
        "estado": "cancelado",
        "mensaje": "El incidente fue cancelado por el cliente.",
        "timestamp": datetime.now().isoformat()
    })
    
    return inc

# ===================================================================
# GET /incidentes/{id} — Obtener un incidente por ID (para Flutter y Angular)
# Este endpoint faltaba y causaba errores 404 en múltiples pantallas
# ===================================================================
@router.get("/{id_incidente}", response_model=IncidenteOut)
def obtener_incidente_por_id(
    id_incidente: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Obtiene los detalles completos de un incidente por su ID."""
    incidente = db.query(Incidente).filter(Incidente.id_incidente == id_incidente).first()
    if not incidente:
        raise HTTPException(status_code=404, detail="Incidente no encontrado.")

    if current_user.tenant_id is not None and incidente.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="No autorizado: El incidente pertenece a otro tenant")

    cliente  = db.query(Usuario).filter(Usuario.id_usuario == incidente.cliente_id).first()
    vehiculo = db.query(Vehiculo).filter(Vehiculo.id_vehiculo == incidente.vehiculo_id).first()
    taller   = db.query(Taller).filter(Taller.id_taller == incidente.taller_actual_id).first() if incidente.taller_actual_id else None
    tecnico  = db.query(Tecnico).filter(Tecnico.id_tecnico == incidente.tecnico_id).first() if incidente.tecnico_id else None
    return incidente


# ===================================================================
# GET /incidentes/{id}/monitoreo — Versión enriquecida para Angular
# Devuelve datos extras: historial_estados, evidencias, taller_nombre, tecnico info
# ===================================================================
@router.get("/{id_incidente}/monitoreo_completo", tags=["CU9 - Monitoreo de Auxilio"])
def monitoreo_completo(
    id_incidente: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Monitoreo completo de un incidente con historial y evidencias."""
    incidente = db.query(Incidente).filter(Incidente.id_incidente == id_incidente).first()
    if not incidente:
        raise HTTPException(status_code=404, detail="Incidente no encontrado")

    if current_user.tenant_id is not None and incidente.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="No autorizado: El incidente pertenece a otro tenant")

    cliente  = db.query(Usuario).filter(Usuario.id_usuario == incidente.cliente_id).first()
    vehiculo = db.query(Vehiculo).filter(Vehiculo.id_vehiculo == incidente.vehiculo_id).first()
    taller   = db.query(Taller).filter(Taller.id_taller == incidente.taller_actual_id).first() if incidente.taller_actual_id else None
    tecnico  = db.query(Tecnico).filter(Tecnico.id_tecnico == incidente.tecnico_id).first() if incidente.tecnico_id else None

    historial = db.query(HistorialEstado).filter(
        HistorialEstado.incidente_id == id_incidente
    ).order_by(HistorialEstado.id_historial.asc()).all()

    return {
        "id_incidente":             incidente.id_incidente,
        "cliente_id":               incidente.cliente_id,
        "vehiculo_id":              incidente.vehiculo_id,
        "taller_actual_id":         incidente.taller_actual_id,
        "tecnico_id":               incidente.tecnico_id,
        "estado_enum":              incidente.estado_enum.value if hasattr(incidente.estado_enum, 'value') else str(incidente.estado_enum),
        "prioridad_enum":           incidente.prioridad_enum.value if hasattr(incidente.prioridad_enum, 'value') else str(incidente.prioridad_enum),
        "descripcion_texto":        incidente.descripcion_texto,
        "latitud_emergencia":       float(incidente.latitud_emergencia) if incidente.latitud_emergencia else None,
        "longitud_emergencia":      float(incidente.longitud_emergencia) if incidente.longitud_emergencia else None,
        "fecha_creacion_timestamp": incidente.fecha_creacion_timestamp.isoformat() if incidente.fecha_creacion_timestamp else None,
        "cliente_nombre":           cliente.nombre if cliente else None,
        "vehiculo_placa":           vehiculo.placa if vehiculo else None,
        "taller_nombre":            taller.nombre if taller else None,
        "taller_telefono":          taller.nit if taller else None,  # Campo teléfono usa NIT como fallback
        "tecnico_nombre":           tecnico.nombre if tecnico else None,
        "tecnico_especialidad":     tecnico.especialidad if tecnico else None,
        "tecnico_telefono":         tecnico.usuario.telefono if (tecnico and tecnico.usuario) else None,
        "clasificacion_ia":         incidente.clasificacion_ia,
        "latitud_tecnico":          float(incidente.latitud_tecnico) if incidente.latitud_tecnico else None,
        "longitud_tecnico":         float(incidente.longitud_tecnico) if incidente.longitud_tecnico else None,
        "latitud_taller":           float(taller.latitud_decimal) if (taller and taller.latitud_decimal) else None,
        "longitud_taller":          float(taller.longitud_decimal) if (taller and taller.longitud_decimal) else None,
        "costo_final_decimal":      float(incidente.costo_final_decimal) if incidente.costo_final_decimal else None,
        "evidencias": [
            {
                "id_evidencia": ev.id_evidencia,
                "tipo":         ev.tipo_enum.value if hasattr(ev.tipo_enum, 'value') else str(ev.tipo_enum),
                "url":          ev.url_recurso,
                "clasificacion": ev.clasificacion_ia_texto,
                "transcripcion": ev.transcripcion_audio_texto,
            }
            for ev in incidente.evidencias
        ],
        "historial_estados": [
            {
                "estado": h.estado_enum.value if hasattr(h.estado_enum, 'value') else str(h.estado_enum),
                "fecha":  h.fecha_hora_timestamp.isoformat() if h.fecha_hora_timestamp else None,
                "comentario": h.comentario_texto,
            }
            for h in historial
        ],
    }


def simular_movimiento_tecnico_background(id_incidente: int, db: Session):
    import time
    # 1. Fetch incident
    incidente = db.query(Incidente).filter(Incidente.id_incidente == id_incidente).first()
    if not incidente:
        return

    # Start coordinates (offset by 0.012 degrees ~ 1.3 km)
    lat_emergencia = float(incidente.latitud_emergencia) if incidente.latitud_emergencia else -17.7833
    lng_emergencia = float(incidente.longitud_emergencia) if incidente.longitud_emergencia else -63.1821

    start_lat = lat_emergencia + 0.012
    start_lng = lng_emergencia - 0.012

    steps = 10
    for i in range(steps + 1):
        fraction = i / steps
        current_lat = start_lat + (lat_emergencia - start_lat) * fraction
        current_lng = start_lng + (lng_emergencia - start_lng) * fraction

        # Update coordinates in database
        incidente.latitud_tecnico = current_lat
        incidente.longitud_tecnico = current_lng
        db.commit()

        # Broadcast coordinate update
        payload = {
            "tipo": "ubicacion_tecnico",
            "latitud": current_lat,
            "longitud": current_lng,
            "timestamp": datetime.now().isoformat()
        }
        asyncio.run(gestor.broadcast(id_incidente, payload))

        # Sleep 0.4 seconds for faster simulation
        time.sleep(0.4)

    # 2. Update status to 'en_atencion'
    incidente.estado_enum = EstadoIncidente.en_atencion
    db.add(HistorialEstado(
        incidente_id=id_incidente,
        estado_enum=EstadoIncidente.en_atencion,
        comentario_texto="Técnico ha llegado al lugar y está atendiendo la emergencia."
    ))
    db.commit()

    # Broadcast status change
    payload_status = {
        "tipo": "cambio_estado",
        "estado": "en_atencion",
        "mensaje": "Técnico en el lugar. Reparando vehículo...",
        "timestamp": datetime.now().isoformat()
    }
    asyncio.run(gestor.broadcast(id_incidente, payload_status))

    # 3. Sleep 7 seconds (simulating repair)
    time.sleep(7)

    # 4. Update status to 'finalizado'
    incidente.estado_enum = EstadoIncidente.finalizado
    incidente.costo_final_decimal = 150.0
    if incidente.tecnico_id:
        tecnico = db.query(Tecnico).filter(Tecnico.id_tecnico == incidente.tecnico_id).first()
        if tecnico:
            tecnico.disponible_boolean = True

    db.add(HistorialEstado(
        incidente_id=id_incidente,
        estado_enum=EstadoIncidente.finalizado,
        comentario_texto="Servicio finalizado con éxito. Costo: Bs. 150."
    ))
    db.commit()

    # Broadcast status change
    payload_final = {
        "tipo": "cambio_estado",
        "estado": "finalizado",
        "mensaje": "Servicio de auxilio finalizado.",
        "costo_final": 150.0,
        "timestamp": datetime.now().isoformat()
    }
    asyncio.run(gestor.broadcast(id_incidente, payload_final))


@router.post("/{id_incidente}/simular", status_code=status.HTTP_200_OK)
def simular_recorrido_incidente(
    id_incidente: int,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Check if incident exists
    incidente = db.query(Incidente).filter(Incidente.id_incidente == id_incidente).first()
    if not incidente:
        raise HTTPException(status_code=404, detail="Incidente no encontrado.")

    # Trigger background simulation
    background_tasks.add_task(simular_movimiento_tecnico_background, id_incidente, db)
    return {"message": "Simulación iniciada en segundo plano."}

