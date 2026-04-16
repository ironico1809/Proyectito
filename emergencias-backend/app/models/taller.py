# ============================================================
# models/taller.py
#
# CONTEXTO DEL PROYECTO:
#   Plataforma Inteligente de Emergencias Vehiculares
#   Backend: FastAPI + PostgreSQL (Supabase)
#   Universidad Autónoma Gabriel René Moreno - SI2 2026
#
# CU3: Gestión de Talleres
#
# Representa la tabla "talleres" de la base de datos.
# SQLAlchemy mapea esta clase a la tabla real en Supabase.
#
# RELACIONES:
#   - dueño_id → FK a usuarios.id_usuario (el taller pertenece a un Usuario con rol 'taller')
#
# ACTORES:
#   A4 (Administrador) → gestiona el CRUD completo de talleres
# ============================================================

from sqlalchemy import Column, Integer, String, Text, Numeric, ForeignKey
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

    # Coordenadas geográficas para el motor de asignación (CU11)
    latitud_decimal   = Column(Numeric(10, 8))
    longitud_decimal  = Column(Numeric(10, 8))

    # Relación con el modelo Usuario (el dueño del taller)
    # Permite acceder a taller.dueno.nombre, taller.dueno.email, etc.
    dueno             = relationship("Usuario", backref="talleres")