from pydantic import BaseModel, Field
from decimal import Decimal
from datetime import datetime
from typing import Optional
from app.models.pago import MetodoPago

class PagoCreate(BaseModel):
    incidente_id: int
    monto_total_decimal: Decimal = Field(..., gt=0, description="Costo total del rescate cobrado al cliente")
    metodo_enum: MetodoPago

class PagoOut(BaseModel):
    id_pago:                    int
    incidente_id:               int
    dueño_taller_id:            int
    monto_total_decimal:        Decimal
    comision_plataforma_decimal: Optional[Decimal] = None
    metodo_enum:                MetodoPago
    estado_pago_enum:           Optional[str] = "completado"
    fecha_pago_timestamp:       Optional[datetime] = None

    class Config:
        from_attributes = True

class StripeIntentCreate(BaseModel):
    incidente_id: int

class StripeIntentOut(BaseModel):
    client_secret: str
    id_intent: str