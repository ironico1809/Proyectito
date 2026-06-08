# app/schemas/ia.py
from pydantic import BaseModel
from app.models.incidente import PrioridadIncidente

class FichaIncidenteIA(BaseModel):
    incidente_id: int
    clasificacion_problema: str
    prioridad_asignada: PrioridadIncidente
    transcripcion_audio: str
    resumen_estructurado: str
    requiere_intervencion_manual: bool