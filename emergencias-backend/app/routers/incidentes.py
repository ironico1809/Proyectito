import math
import requests
import base64
import json
import os
from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel
from app.models.pago import Pago
from app.database import get_db, SessionLocal
from app.models.usuario import Usuario, TipoRol
from app.models.vehiculo import Vehiculo
from app.models.taller import Taller
from app.models.tecnico import Tecnico
from app.models.incidente import Incidente, EvidenciaIA, HistorialEstado, EstadoIncidente, TipoEvidencia, PrioridadIncidente
from app.schemas.incidente import IncidenteCreate, IncidenteOut, AccionSolicitud, AsignarTecnico, ActualizarEstado
from app.routers.auth import get_current_user
from app.routers.notificaciones import crear_notificacion_interna
from apscheduler.schedulers.background import BackgroundScheduler

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
    """SALVAVIDAS EXTREMO: Si Groq se cae por completo, Python clasifica el texto."""
    texto_total = f"{descripcion} {transcripcion}".lower()
    
    clasificacion = "otros"
    prioridad = "incierto"
    resumen = "Evaluación técnica requerida."

    if any(palabra in texto_total for palabra in ["llan", "pinch", "tire", "goma", "flat", "rueda"]):
        clasificacion = "llanta"
        prioridad = "media"
        resumen = "Problema de neumático detectado."
    elif any(palabra in texto_total for palabra in ["cho", "acciden", "golp", "crash", "damage"]):
        clasificacion = "choque"
        prioridad = "alta"
        resumen = "Colisión vehicular detectada."
    elif any(palabra in texto_total for palabra in ["bat", "arran", "encien", "electr", "battery"]):
        clasificacion = "bateria"
        prioridad = "media"
        resumen = "Posible descarga de batería."
    elif any(palabra in texto_total for palabra in ["mot", "hum", "calien", "radia", "engine"]):
        clasificacion = "motor"
        prioridad = "alta"
        resumen = "Falla de motor o sobrecalentamiento."

    texto_final = f"[{clasificacion.upper()}] Prioridad {prioridad.upper()}: {resumen}"
    return texto_final[:95], prioridad

def analizar_emergencia_groq(b64_img: str, descripcion: str, transcripcion: str):
    """Usa IA Visual. Si un modelo está apagado, salta automáticamente al siguiente."""
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json"
    }
    
    texto_prompt = f"""
    Eres un perito experto en vehículos. Analiza la siguiente emergencia.
    Descripción del cliente: "{descripcion}"
    Lo que el cliente dijo en el audio: "{transcripcion}"
    
    Devuelve ESTRICTAMENTE un JSON válido con esta estructura:
    {{
        "resumen": "Resumen clínico y profesional de 1 línea.",
        "clasificacion": "choque", // Elige SOLO UNA: bateria, llanta, choque, motor, otros
        "prioridad": "alta" // Elige SOLO UNA: alta, media, baja, incierto
    }}
    Solo devuelve el JSON puro, sin comillas invertidas ni explicaciones.
    """

    content_array = [{"type": "text", "text": texto_prompt}]
    if b64_img:
        content_array.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{b64_img}"}
        })

    modelos_activos = [
        "llama-3.2-90b-vision-preview",
        "llama-3.2-11b-vision",
        "meta-llama/llama-4-scout-17b-16e-instruct"
    ]

    for modelo in modelos_activos:
        payload = {
            "model": modelo,
            "messages": [{"role": "user", "content": content_array}],
            "temperature": 0.2
        }

        try:
            res = requests.post(url, headers=headers, json=payload, timeout=10)
            if res.status_code == 200:
                texto_ia = res.json()["choices"][0]["message"]["content"]
                texto_limpio = texto_ia.replace("```json", "").replace("```", "").strip()
                dict_ia = json.loads(texto_limpio)
                
                clasificacion = dict_ia.get("clasificacion", "otros").upper()
                prioridad = dict_ia.get("prioridad", "incierto").lower()
                resumen = dict_ia.get("resumen", "Análisis completado.")
                
                texto_final = f"[{clasificacion}] Prioridad {prioridad.upper()}: {resumen}"
                return texto_final[:95], prioridad
            else:
                print(f"Error Groq con {modelo}: {res.text}")
        except Exception as e:
            print(f"Excepción Groq con {modelo}: {e}")

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
    a = math.sin(dlat / 2)**2 + math.cos(math.radians(float(lat1))) * math.cos(math.radians(float(lat2))) * math.sin(dlon / 2)**2
    return R * (2 * math.atan2(math.sqrt(a), math.sqrt(1 - a)))

def buscar_taller_disponible(db: Session, lat_emergencia, lon_emergencia, incidente_id: int = None):
    excluidos = []
    if incidente_id:
        historial = db.query(HistorialEstado.comentario_texto).filter(HistorialEstado.incidente_id == incidente_id).all()
        excluidos = [h[0] for h in historial if "Taller ID:" in h[0]]

    talleres = db.query(Taller).all()
    mejor_taller, dist_min = None, float('inf')

    for t in talleres:
        if f"Taller ID: {t.id_taller}" in str(excluidos): continue
        if db.query(Tecnico).filter(Tecnico.taller_id == t.id_taller, Tecnico.disponible_boolean == True).first():
            d = calcular_distancia(lat_emergencia, lon_emergencia, t.latitud_decimal, t.longitud_decimal)
            if d < dist_min: dist_min, mejor_taller = d, t
    return mejor_taller, dist_min

def robot_reasignacion_automatica():
    db = SessionLocal()
    try:
        ahora = datetime.now()
        estancados = db.query(Incidente).filter(Incidente.estado_enum == EstadoIncidente.pendiente, Incidente.fecha_creacion_timestamp <= ahora - timedelta(minutes=5)).all()
        for inc in estancados:
            nuevo_taller, dist = buscar_taller_disponible(db, inc.latitud_emergencia, inc.longitud_emergencia, inc.id_incidente)
            if nuevo_taller:
                msg = f"Ventana expirada. Reasignado a Taller ID: {nuevo_taller.id_taller}"
                inc.taller_actual_id = nuevo_taller.id_taller
                inc.fecha_creacion_timestamp = ahora
                crear_notificacion_interna(db, nuevo_taller.dueño_id, "🚨 Alerta Reasignada", "Un taller no respondió a tiempo.")
            else:
                msg = "Ventana expirada. No hay más talleres disponibles."
                inc.taller_actual_id = None
                
            db.add(HistorialEstado(incidente_id=inc.id_incidente, estado_enum=EstadoIncidente.pendiente, comentario_texto=msg))
            db.commit()
    finally:
        db.close()

scheduler = BackgroundScheduler()
scheduler.add_job(robot_reasignacion_automatica, 'interval', minutes=1)
scheduler.start()

class UbicacionTecnicoUpdate(BaseModel):
    latitud: float
    longitud: float

@router.put("/{id_incidente}/ubicacion-tecnico")
def actualizar_ubicacion_tecnico(id_incidente: int, datos: UbicacionTecnicoUpdate, db: Session = Depends(get_db)):
    incidente = db.query(Incidente).filter(Incidente.id_incidente == id_incidente).first()
    if incidente:
        incidente.latitud_tecnico = datos.latitud
        incidente.longitud_tecnico = datos.longitud
        db.commit()
    return {"status": "ok"}

# ===================================================================
# REGISTRAR EMERGENCIA (Guardado Blindado en BD)
# ===================================================================
@router.post("/", response_model=IncidenteOut, status_code=status.HTTP_201_CREATED)
def registrar_emergencia(datos: IncidenteCreate, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    vehiculo = db.query(Vehiculo).filter(Vehiculo.id_vehiculo == datos.vehiculo_id, Vehiculo.usuario_id == current_user.id_usuario).first()
    if not vehiculo: raise HTTPException(status_code=403, detail="Acceso denegado al vehículo.")

    taller, dist = buscar_taller_disponible(db, datos.latitud_emergencia, datos.longitud_emergencia)

    nuevo_incidente = Incidente(
        cliente_id=current_user.id_usuario,
        vehiculo_id=datos.vehiculo_id,
        taller_actual_id=taller.id_taller if taller else None,
        latitud_emergencia=datos.latitud_emergencia,
        longitud_emergencia=datos.longitud_emergencia,
        descripcion_texto=datos.descripcion_texto
    )
    db.add(nuevo_incidente)
    db.flush() 

    evidencias_a_procesar = datos.evidencias if datos.evidencias else []
    b64_img = None
    audio_bytes = None
    
    for ev in evidencias_a_procesar:
        tipo_str = str(ev.tipo_enum.value) if hasattr(ev.tipo_enum, 'value') else str(ev.tipo_enum)
        url = ev.url_recurso if hasattr(ev, 'url_recurso') else ev.get("url_recurso", "")
        
        if "imagen" in tipo_str and url.startswith("data:image"):
            b64_img = url.split(",")[1]
        elif "audio" in tipo_str and url.startswith("data:audio"):
            try:
                audio_bytes = base64.b64decode(url.split(",")[1])
            except Exception:
                pass

    texto_cliente = datos.descripcion_texto or ""
    transcripcion = ""
    
    # 1. Transcribimos Audio (Nunca falla)
    if audio_bytes:
        transcripcion = transcribir_audio_groq(audio_bytes)
        
    # 2. Analizamos con la IA Visual y Textual (Imposible que tire error)
    texto_resumen_seguro, prioridad_ia = analizar_emergencia_groq(b64_img, texto_cliente, transcripcion)

    try:
        nuevo_incidente.prioridad_enum = PrioridadIncidente(prioridad_ia)
    except ValueError:
        nuevo_incidente.prioridad_enum = PrioridadIncidente.incierto

    # 3. Guardamos en BD
    for ev in evidencias_a_procesar:
        tipo_raw = ev.tipo_enum if hasattr(ev, 'tipo_enum') else ev["tipo_enum"]
        tipo_str = str(tipo_raw.value) if hasattr(tipo_raw, 'value') else str(tipo_raw)
        url = ev.url_recurso if hasattr(ev, 'url_recurso') else ev["url_recurso"]
        
        transcripcion_guardar = None
        if "audio" in tipo_str:
            transcripcion_guardar = transcripcion if transcripcion else "Audio procesado."

        nueva_evidencia = EvidenciaIA(
            incidente_id=nuevo_incidente.id_incidente, 
            tipo_enum=tipo_raw, 
            url_recurso=url, 
            clasificacion_ia_texto=texto_resumen_seguro, 
            nivel_confianza=0.98,
            transcripcion_audio_texto=transcripcion_guardar 
        )
        db.add(nueva_evidencia)

    comentario = f"Alerta enviada a Taller ID: {taller.id_taller} ({dist:.2f}km)" if taller else "Buscando taller..."
    db.add(HistorialEstado(incidente_id=nuevo_incidente.id_incidente, estado_enum=EstadoIncidente.pendiente, comentario_texto=comentario))
    crear_notificacion_interna(db, current_user.id_usuario, "Emergencia Registrada", "La IA procesó tu caso.")
    if taller: crear_notificacion_interna(db, taller.dueño_id, "🚨 Nueva Alerta", f"Vehículo a {dist:.2f}km.")

    db.commit()
    db.refresh(nuevo_incidente)
    return nuevo_incidente

# ===================================================================
# DEMÁS ENDPOINTS REST API
# ===================================================================
@router.get("/pendientes", response_model=List[IncidenteOut])
def listar_solicitudes_pendientes(db: Session = Depends(get_db)):
    return db.query(Incidente).filter(Incidente.estado_enum == EstadoIncidente.pendiente).all()

@router.post("/{id_incidente}/accion")
def responder_solicitud(id_incidente: int, datos: AccionSolicitud, db: Session = Depends(get_db)):
    incidente = db.query(Incidente).filter(Incidente.id_incidente == id_incidente).first()
    if not incidente or incidente.estado_enum != EstadoIncidente.pendiente:
        raise HTTPException(status_code=400, detail="El incidente ya no está disponible.")
    
    if datos.accion == "aceptar":
        incidente.estado_enum = EstadoIncidente.en_proceso
        db.add(HistorialEstado(incidente_id=id_incidente, estado_enum=EstadoIncidente.en_proceso, comentario_texto="Solicitud aceptada por el Taller."))
        crear_notificacion_interna(db, incidente.cliente_id, "¡Auxilio en camino!", "Tu solicitud ha sido aceptada.")

    elif datos.accion == "rechazar":
        nuevo_taller, dist = buscar_taller_disponible(db, incidente.latitud_emergencia, incidente.longitud_emergencia, id_incidente)
        if nuevo_taller:
            incidente.taller_actual_id = nuevo_taller.id_taller
            incidente.fecha_creacion_timestamp = datetime.now()
            db.add(HistorialEstado(incidente_id=id_incidente, estado_enum=EstadoIncidente.pendiente, comentario_texto=f"Reasignado a Taller ID: {nuevo_taller.id_taller}"))
            crear_notificacion_interna(db, nuevo_taller.dueño_id, "🚨 Emergencia Derivada", f"Un incidente a {dist:.2f}km ha sido derivado a tu taller.")
        else:
            incidente.taller_actual_id = None
            db.add(HistorialEstado(incidente_id=id_incidente, estado_enum=EstadoIncidente.pendiente, comentario_texto="Rechazado. No hay más talleres disponibles en la zona."))
            
    db.commit()
    return {"status": "ok"}

@router.post("/{id_incidente}/asignar")
def asignar_tecnico(id_incidente: int, datos: AsignarTecnico, db: Session = Depends(get_db)):
    incidente = db.query(Incidente).filter(Incidente.id_incidente == id_incidente).first()
    tecnico = db.query(Tecnico).filter(Tecnico.id_tecnico == datos.tecnico_id).first()

    if not tecnico or not tecnico.disponible_boolean:
        raise HTTPException(status_code=400, detail="El técnico no está disponible.")

    incidente.tecnico_id = datos.tecnico_id
    tecnico.disponible_boolean = False 
    db.add(HistorialEstado(incidente_id=id_incidente, estado_enum=EstadoIncidente.en_proceso, comentario_texto=f"Técnico {tecnico.nombre} despachado hacia el lugar."))
    crear_notificacion_interna(db, incidente.cliente_id, "Técnico Asignado", f"El mecánico {tecnico.nombre} va en ruta.")
    db.commit()
    return {"message": "Técnico asignado exitosamente."}

@router.get("/en-proceso", response_model=List[IncidenteOut])
def listar_solicitudes_en_proceso(db: Session = Depends(get_db)):
    return db.query(Incidente).filter(Incidente.estado_enum == EstadoIncidente.en_proceso).all()

@router.put("/{id_incidente}/estado", status_code=status.HTTP_200_OK)
def actualizar_estado_servicio(id_incidente: int, datos: ActualizarEstado, db: Session = Depends(get_db)):
    incidente = db.query(Incidente).filter(Incidente.id_incidente == id_incidente).first()
    if not incidente: raise HTTPException(status_code=404, detail="Incidente no encontrado.")

    incidente.estado_enum = datos.estado_enum
       
    if datos.estado_enum == EstadoIncidente.atendido:
        if incidente.tecnico_id:
            tecnico = db.query(Tecnico).filter(Tecnico.id_tecnico == incidente.tecnico_id).first()
            if tecnico: tecnico.disponible_boolean = True 
            
        if datos.costo_final is not None:
            incidente.costo_final_decimal = datos.costo_final

    db.add(HistorialEstado(incidente_id=id_incidente, estado_enum=datos.estado_enum, comentario_texto=datos.comentario or f"Servicio actualizado a {datos.estado_enum.value}."))
    crear_notificacion_interna(db, incidente.cliente_id, "Actualización de Servicio", f"El estado de tu emergencia ahora es: {datos.estado_enum.value.upper()}")
    db.commit()
    return {"message": "Estado actualizado correctamente", "nuevo_estado": incidente.estado_enum}

@router.get("/{id_incidente}/monitoreo", tags=["CU9 - Monitoreo de Auxilio"])
def monitorear_auxilio(id_incidente: int, db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    incidente = db.query(Incidente).filter(Incidente.id_incidente == id_incidente).first()
    if not incidente: raise HTTPException(status_code=404, detail="Incidente no encontrado")
        
    respuesta = {
        "id_incidente": incidente.id_incidente,
        "estado_actual": incidente.estado_enum.value,
        "prioridad": incidente.prioridad_enum.value,
        "latitud_tecnico": float(incidente.latitud_tecnico) if incidente.latitud_tecnico else None,
        "longitud_tecnico": float(incidente.longitud_tecnico) if incidente.longitud_tecnico else None,
        # 🔥 AQUÍ ESTÁ LA SOLUCIÓN: Ahora el backend devuelve el precio al teléfono del cliente
        "costo_final_decimal": float(incidente.costo_final_decimal) if incidente.costo_final_decimal else 0.0,
        "tecnico_asignado": None,
        "taller_responsable": None
    }

    if incidente.tecnico_id:
        tecnico = db.query(Tecnico).filter(Tecnico.id_tecnico == incidente.tecnico_id).first()
        if tecnico:
            respuesta["tecnico_asignado"] = {"nombre": tecnico.nombre, "especialidad": tecnico.especialidad}
            taller = db.query(Taller).filter(Taller.id_taller == tecnico.taller_id).first()
            if taller: respuesta["taller_responsable"] = taller.nombre

    return respuesta

@router.get("/cliente/activo", tags=["CU9 - Monitoreo de Auxilio"])
def obtener_emergencia_activa(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    incidente = db.query(Incidente).filter(
        Incidente.cliente_id == current_user.id_usuario,
        Incidente.estado_enum != EstadoIncidente.cancelado
    ).order_by(Incidente.id_incidente.desc()).first()

    if incidente:
        if incidente.estado_enum == EstadoIncidente.atendido:
            pago_existente = db.query(Pago).filter(Pago.incidente_id == incidente.id_incidente).first()
            if pago_existente:
                return {"id_incidente": None} # Ya pagó, el ciclo está 100% cerrado
        
        return {"id_incidente": incidente.id_incidente}
    
    return {"id_incidente": None}

@router.get("/historial/tecnico/{id_tecnico}", tags=["CU12 - Técnico de Auxilio"])
def obtener_historial_tecnico(
    id_tecnico: int, 
    db: Session = Depends(get_db), 
    current_user: Usuario = Depends(get_current_user)
):
    tecnico = db.query(Tecnico).filter(Tecnico.usuario_id == current_user.id_usuario).first()
    
    if not tecnico:
        return [] # Si el usuario no es técnico, devolvemos vacío para no crashear

    incidentes = db.query(Incidente).filter(
        Incidente.tecnico_id == tecnico.id_tecnico,
    ).order_by(Incidente.fecha_creacion_timestamp.desc()).all()

    resultado = []
    
    for inc in incidentes:
        cliente = db.query(Usuario).filter(Usuario.id_usuario == inc.cliente_id).first()
        vehiculo = db.query(Vehiculo).filter(Vehiculo.id_vehiculo == inc.vehiculo_id).first()
        
        nombre_cliente = cliente.nombre if cliente else "Cliente Anónimo"
        modelo_vehiculo = f"{vehiculo.marca} {vehiculo.modelo}" if vehiculo else "Sin registrar"

        resultado.append({
            "id_incidente": inc.id_incidente,
            "fecha_creacion_timestamp": inc.fecha_creacion_timestamp,
            "estado_enum": inc.estado_enum if hasattr(inc.estado_enum, 'value') else str(inc.estado_enum), 
            "cliente_nombre": nombre_cliente,   
            "vehiculo_modelo": modelo_vehiculo  
        })

    return resultado