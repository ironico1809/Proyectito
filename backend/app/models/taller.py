# ============================================================
# models/taller.py
#
#
# CU3: Gestión de Talleres
# ============================================================
from sqlalchemy import Column, Integer, String, Text, DECIMAL, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Taller(Base):
    __tablename__ = "talleres"

    id_taller         = Column(Integer, primary_key=True, index=True)
    dueño_id          = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)

    nombre            = Column(String(150), nullable=False)
    direccion         = Column(Text)
    nit               = Column(String(50))

    latitud_decimal   = Column(DECIMAL(10, 8))
    longitud_decimal  = Column(DECIMAL(10, 8))
    tenant_id         = Column(Integer, ForeignKey("tenants.id_tenant"), nullable=True, default=1)

    dueno             = relationship("Usuario", backref="talleres", foreign_keys=[dueño_id])
    tecnicos          = relationship("Tecnico", back_populates="taller", cascade="all, delete")
    tenant            = relationship("Tenant", foreign_keys=[tenant_id])

class TallerInventario(Base):
    __tablename__ = "taller_inventario"

    id_inventario = Column(Integer, primary_key=True, index=True)
    taller_id     = Column(Integer, ForeignKey("talleres.id_taller"), nullable=False)
    item_nombre   = Column(String(100), nullable=False) # Ej: "batería", "llanta"
    cantidad      = Column(Integer, default=0)

    taller        = relationship("Taller", backref="inventario")


    