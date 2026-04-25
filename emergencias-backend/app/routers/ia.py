# ============================================================
# routers/ia.py
#
# CU8: Diagnóstico y Resumen Inteligente (IA)

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.incidente import Incidente, EvidenciaIA, HistorialEstado, PrioridadIncidente, EstadoIncidente, TipoEvidencia
from app.schemas.ia import FichaIncidenteIA

router = APIRouter(prefix="/ia", tags=["CU8 - Procesamiento Multimodal (IA)"])

@router.post("/diagnosticar/{id_incidente}", response_model=FichaIncidenteIA, status_code=status.HTTP_200_OK)
def procesar_diagnostico_ia(id_incidente: int, db: Session = Depends(get_db)):
    
    incidente = db.query(Incidente).filter(Incidente.id_incidente == id_incidente).first()
    if not incidente:
        raise HTTPException(status_code=404, detail="Incidente no encontrado")
        
    evidencias = db.query(EvidenciaIA).filter(EvidenciaIA.incidente_id == id_incidente).all()
    texto_analisis = (incidente.descripcion_texto or "").lower()
    
    clasificacion = "otros"
    prioridad = PrioridadIncidente.incierto
    resumen = "Información poco clara. Se requiere intervención manual."
    intervencion_manual = True

    if "bateria" in texto_analisis or "batería" in texto_analisis or "no enciende" in texto_analisis:
        clasificacion = "batería"
        prioridad = PrioridadIncidente.media
        resumen = "Vehículo no responde. Posible fallo eléctrico o batería descargada. Se sugiere taller con auxilio eléctrico."
        intervencion_manual = False
        
    elif "llanta" in texto_analisis or "pinchazo" in texto_analisis:
        clasificacion = "llanta"
        prioridad = PrioridadIncidente.media
        resumen = "Daño en neumático reportado. Incidente leve. Se requiere taller cercano con servicio móvil o llantería."
        intervencion_manual = False
        
    elif "choque" in texto_analisis or "accidente" in texto_analisis or "golpe" in texto_analisis:
        clasificacion = "choque"
        prioridad = PrioridadIncidente.alta
        resumen = "Colisión vehicular detectada. Posible daño estructural. Se sugiere taller con capacidad de remolque/grúa."
        intervencion_manual = False

    incidente.prioridad_enum = prioridad
    
    if evidencias:
        for ev in evidencias:
            ev.clasificacion_ia_texto = clasificacion
            if ev.tipo_enum == TipoEvidencia.audio:
                ev.transcripcion_audio_texto = texto_analisis 

    ficha_generada = FichaIncidenteIA(
        incidente_id=incidente.id_incidente,
        clasificacion_problema=clasificacion,
        prioridad_asignada=prioridad,
        transcripcion_audio=texto_analisis if texto_analisis else "Sin audio",
        resumen_estructurado=resumen,
        requiere_intervencion_manual=intervencion_manual
    )

    historial = HistorialEstado(
        incidente_id=incidente.id_incidente,
        estado_enum=EstadoIncidente.pendiente, # CORRECCIÓN AQUÍ 👇 (estado_enum en vez de estado_incidente)
        comentario_texto=f"IA completó análisis. Clasificación: {clasificacion.upper()}. Prioridad: {prioridad.value.upper()}."
    )
    
    db.add(historial)
    db.commit()
    db.refresh(incidente)

    return ficha_generada