from sqlalchemy import Column, Integer, String, ForeignKey, Enum as SAEnum, DECIMAL, TIMESTAMP, FetchedValue
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

class MetodoPago(str, enum.Enum):
    transferencia = "transferencia"
    qr = "qr"
    tarjeta = "tarjeta"
    paypal = "paypal"

class Pago(Base):
    __tablename__ = "pagos"

    id_pago = Column(Integer, primary_key=True, index=True)
    incidente_id = Column(Integer, ForeignKey("incidentes.id_incidente"), unique=True)
    dueño_taller_id = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False) # 🔗 El vínculo al Tallerista
    monto_total_decimal = Column(DECIMAL(10, 2), nullable=False)
    comision_plataforma_decimal = Column(DECIMAL(10, 2), server_default=FetchedValue())
    
    metodo_enum = Column(SAEnum(MetodoPago, name="metodo_pago"), nullable=False)
    estado_pago_enum = Column(String(20), default="completado")
    fecha_pago_timestamp = Column(TIMESTAMP, server_default=func.now())

    incidente = relationship("Incidente")
    dueño = relationship("Usuario")