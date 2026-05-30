from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from decimal import Decimal

class CotizacionCreate(BaseModel):
    incidente_id: int
    precio_estimado: Decimal
    tiempo_estimado_min: int
    descripcion: Optional[str] = None

class CotizacionResponse(BaseModel):
    id_cotizacion: int
    incidente_id: int
    taller_id: int
    precio_estimado: Decimal
    tiempo_estimado_min: int
    descripcion: Optional[str]
    estado: str
    fecha_envio: datetime
    fecha_respuesta: Optional[datetime]

    class Config:
        from_attributes = True