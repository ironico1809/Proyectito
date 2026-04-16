# ============================================================
# models/incidente.py
#
# CONTEXTO DEL PROYECTO:
#   Plataforma Inteligente de Emergencias Vehiculares
#   Backend: FastAPI + PostgreSQL (Supabase)
#
# CU7: Registrar Emergencia Multimodal
#
# Representa las tablas centrales del sistema:
#   1. incidentes
#   2. evidencias_ia (audios, fotos)
#   3. historial_estados (trazabilidad)
# ============================================================

import enum
from sqlalchemy import Column, Integer, String, Text, Numeric, ForeignKey, DateTime, Enum as SAEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base

# -------------------------------------------------------
# ENUMS (Tipos de datos estrictos según Script BD - Pag 28)
# -------------------------------------------------------
class EstadoIncidente(str, enum.Enum):
    pendiente  = "pendiente"
    en_proceso = "en proceso"
    atendido   = "atendido"

class PrioridadIncidente(str, enum.Enum):
    baja     = "baja"
    media    = "media"
    alta     = "alta"
    incierto = "incierto" # Valor por defecto hasta que la IA lo analice

class TipoEvidencia(str, enum.Enum):
    audio  = "audio"
    imagen = "imagen"
    texto  = "texto"


# -------------------------------------------------------
# TABLA PRINCIPAL: Incidentes
# -------------------------------------------------------
class Incidente(Base):
    __tablename__ = "incidentes"

    id_incidente        = Column(Integer, primary_key=True, index=True)
    cliente_id          = Column(Integer, ForeignKey("usuarios.id_usuario"), nullable=False)
    vehiculo_id         = Column(Integer, ForeignKey("vehiculos.id_vehiculo"), nullable=False)
    
    # El técnico es NULL al inicio, se llena en el CU11 (Asignación)
    tecnico_id          = Column(Integer, ForeignKey("tecnicos.id_tecnico"), nullable=True) 
    
    # Timestamp automático del servidor
    fecha_creacion_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    
    estado_enum         = Column(SAEnum(EstadoIncidente, name="estado_incidente"), default=EstadoIncidente.pendiente)
    prioridad_enum      = Column(SAEnum(PrioridadIncidente, name="prioridad_incidente"), default=PrioridadIncidente.incierto)
    
    descripcion_texto   = Column(Text, nullable=True)
    latitud_emergencia  = Column(Numeric(10, 8), nullable=False)
    longitud_emergencia = Column(Numeric(10, 8), nullable=False)

    # Relaciones para que FastAPI traiga las listas automáticamente
    evidencias = relationship("EvidenciaIA", backref="incidente", cascade="all, delete-orphan")
    historial  = relationship("HistorialEstado", backref="incidente", cascade="all, delete-orphan")


# -------------------------------------------------------
# TABLA SECUNDARIA: Evidencias IA (Fotos, Audios)
# -------------------------------------------------------
class EvidenciaIA(Base):
    __tablename__ = "evidencias_ia"

    id_evidencia              = Column(Integer, primary_key=True, index=True)
    incidente_id              = Column(Integer, ForeignKey("incidentes.id_incidente", ondelete="CASCADE"), nullable=False)
    tipo_enum                 = Column(SAEnum(TipoEvidencia, name="tipo_evidencia"), nullable=False)
    url_recurso               = Column(Text, nullable=False) # URL del bucket de Supabase Storage
    transcripcion_audio_texto = Column(Text, nullable=True)
    clasificacion_ia_texto    = Column(String(100), nullable=True)
    nivel_confianza           = Column(Numeric(5, 2), nullable=True)


# -------------------------------------------------------
# TABLA SECUNDARIA: Historial de Estados (Trazabilidad)
# -------------------------------------------------------
class HistorialEstado(Base):
    __tablename__ = "historial_estados"

    id_historial         = Column(Integer, primary_key=True, index=True)
    incidente_id         = Column(Integer, ForeignKey("incidentes.id_incidente", ondelete="CASCADE"), nullable=False)
    estado_incidente     = Column(SAEnum(EstadoIncidente, name="estado_incidente"), nullable=False)
    fecha_hora_timestamp = Column(DateTime(timezone=True), server_default=func.now())
    comentario_texto     = Column(Text, nullable=True)