# ============================================================
# models/tecnico.py
#
# CONTEXTO DEL PROYECTO:
#   Plataforma Inteligente de Emergencias Vehiculares
#
# TABLA QUE REPRESENTA:
#   - tecnicos → Personal mecánico de cada taller
#
# CU6: Administrar Staff Técnico (CRUD)
#   Actor: A2 (Taller)
#   El taller registra, edita y gestiona disponibilidad
#   de sus técnicos desde la app web Angular
#
# RELACIÓN:
#   Un taller tiene muchos técnicos (1:N)
#   Un técnico atiende muchos incidentes (1:N)
# ============================================================

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base

class Tecnico(Base):
    __tablename__ = "tecnicos"

    id_tecnico         = Column(Integer, primary_key=True, index=True)
    taller_id          = Column(Integer, ForeignKey("talleres.id_taller", ondelete="CASCADE"))
    
    # ⚡ VÍNCULO CON LA CUENTA DE USUARIO
    usuario_id         = Column(Integer, ForeignKey("usuarios.id_usuario", ondelete="CASCADE"), nullable=False)
    
    # ⚡ ESTA ES LA LÍNEA QUE FALTABA (Sin esto da TypeError)
    nombre             = Column(String(100), nullable=False) 
    
    especialidad       = Column(String(100), nullable=True)
    disponible_boolean = Column(Boolean, default=True)

    # Relaciones
    taller  = relationship("Taller", back_populates="tecnicos")
    usuario = relationship("Usuario")