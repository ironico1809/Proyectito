# ============================================================
# models/vehiculo.py
#
# CU5: Administrar Vehículos
#
from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Vehiculo(Base):
    __tablename__ = "vehiculos"

    id_vehiculo = Column(Integer, primary_key=True, index=True)
    
    usuario_id  = Column(Integer, ForeignKey("usuarios.id_usuario", ondelete="CASCADE"), nullable=False) 
    placa       = Column(String(20), unique=True, nullable=False)
    marca       = Column(String(50))
    modelo      = Column(String(50))
    color       = Column(String(30))

    
    propietario = relationship("Usuario", backref="vehiculos")