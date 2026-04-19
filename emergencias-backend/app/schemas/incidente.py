# ============================================================
# schemas/incidente.py
#
# CONTEXTO DEL PROYECTO:
#   Validación de datos de entrada/salida para el flujo principal.
#
# NOTA PARA EL EQUIPO FRONTEND (ANGULAR / FLUTTER):
#   - Flutter (CU7): Enviar el objeto 'IncidenteCreate'. 'evidencias' es un Array.
#   - Angular (CU10): Enviar 'AccionSolicitud' con "aceptar" o "rechazar".
# ============================================================

from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal
from datetime import datetime
from app.models.incidente import EstadoIncidente, PrioridadIncidente, TipoEvidencia

# -------------------------------------------------------
# ENTRADAS: Lo que el Frontend envía al Backend
# -------------------------------------------------------

class EvidenciaCreate(BaseModel):
    tipo_enum:   TipoEvidencia
    url_recurso: str # Link del archivo subido a Supabase Storage

class IncidenteCreate(BaseModel):
    vehiculo_id:         int
    latitud_emergencia:  Decimal
    longitud_emergencia: Decimal
    descripcion_texto:   Optional[str] = None
    evidencias:          List[EvidenciaCreate] = [] # Soporta múltiples fotos/audios

class AccionSolicitud(BaseModel):
    accion:     str  # Solo debe ser "aceptar" o "rechazar"
    comentario: Optional[str] = None

class AsignarTecnico(BaseModel):
    tecnico_id: int
class ActualizarEstado(BaseModel):
    estado_enum: EstadoIncidente
    comentario: Optional[str] = None
# -------------------------------------------------------
# SALIDAS: Lo que el Backend responde al Frontend
# -------------------------------------------------------

class EvidenciaOut(BaseModel):
    id_evidencia:           int
    tipo_enum:              TipoEvidencia
    url_recurso:            str
    clasificacion_ia_texto: Optional[str] = None
    nivel_confianza:        Optional[Decimal] = None

    class Config:
        from_attributes = True

class IncidenteOut(BaseModel):
    id_incidente:             int
    cliente_id:               int
    vehiculo_id:              int
    tecnico_id:               Optional[int] = None
    estado_enum:              EstadoIncidente
    prioridad_enum:           PrioridadIncidente
    descripcion_texto:        Optional[str] = None
    latitud_emergencia:       Decimal
    longitud_emergencia:      Decimal
    fecha_creacion_timestamp: datetime
    
    # Anidamos las evidencias para que viajen junto con el incidente
    evidencias:               List[EvidenciaOut] = []

    class Config:
        from_attributes = True
