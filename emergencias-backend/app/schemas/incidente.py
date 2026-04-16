# ============================================================
# schemas/incidente.py
#
# CU7: Registrar Emergencia Multimodal
#
# NOTA PARA EL EQUIPO FRONTEND (ANGULAR / FLUTTER):
#   Al diseñar las interfaces responsivas, recuerden que 
#   'evidencias' es un Array (Lista). El diseño debe adaptarse 
#   para mostrar 0, 1 o múltiples fotos/audios en forma de grid 
#   o carrusel en móviles y tablets.
# ============================================================

from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal
from datetime import datetime
from app.models.incidente import EstadoIncidente, PrioridadIncidente, TipoEvidencia

# -------------------------------------------------------
# ESTRUCTURAS DE ENTRADA (Lo que envía el Frontend)
# -------------------------------------------------------
class EvidenciaCreate(BaseModel):
    tipo_enum: TipoEvidencia
    url_recurso: str  # Frontend sube el archivo a Supabase y nos manda el link

class IncidenteCreate(BaseModel):
    vehiculo_id: int
    latitud_emergencia: Decimal
    longitud_emergencia: Decimal
    descripcion_texto: Optional[str] = None
    evidencias: List[EvidenciaCreate] = [] # Lista opcional de archivos adjuntos

# -------------------------------------------------------
# ESTRUCTURAS DE SALIDA (Lo que responde el Backend)
# -------------------------------------------------------
class EvidenciaOut(BaseModel):
    id_evidencia: int
    tipo_enum: TipoEvidencia
    url_recurso: str
    clasificacion_ia_texto: Optional[str] = None

    class Config:
        from_attributes = True

class IncidenteOut(BaseModel):
    id_incidente: int
    cliente_id: int
    vehiculo_id: int
    estado_enum: EstadoIncidente
    prioridad_enum: PrioridadIncidente
    latitud_emergencia: Decimal
    longitud_emergencia: Decimal
    fecha_creacion_timestamp: datetime
    
    # Anidamos las evidencias en la respuesta
    evidencias: List[EvidenciaOut] = []

    class Config:
        from_attributes = True