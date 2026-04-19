# ============================================================
# models/taller.py
#
# CONTEXTO DEL PROYECTO:
#   Plataforma Inteligente de Emergencias Vehiculares
#   Backend: FastAPI + PostgreSQL (Supabase)
#   Universidad Autónoma Gabriel René Moreno - SI2 2026
#
# CU3: Gestión de Talleres
# ============================================================

# CORRECCIÓN: Importar DECIMAL en lugar de Numeric
from sqlalchemy import Column, Integer, String, Text, DECIMAL, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base


class Taller(Base):
    __tablename__ = "talleres"

    # Clave primaria autoincremental
    id_taller         = Column(Integer, primary_key=True, index=True)

    # FK al usuario dueño del taller (debe tener rol='taller')
    dueño_id          = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)

    # Datos del taller
    nombre            = Column(String(150), nullable=False)
    direccion         = Column(Text)
    nit               = Column(String(50))

    # CORRECCIÓN: Usar DECIMAL para coincidir con tu script de BD
    latitud_decimal   = Column(DECIMAL(10, 8))
    longitud_decimal  = Column(DECIMAL(10, 8))

    # Relaciones
    dueno             = relationship("Usuario", backref="talleres")
    tecnicos          = relationship("Tecnico", back_populates="taller", cascade="all, delete")