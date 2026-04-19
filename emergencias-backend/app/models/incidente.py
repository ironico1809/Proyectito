# ============================================================
# models/incidente.py
#
# CONTEXTO DEL PROYECTO:
#   Plataforma Inteligente de Emergencias Vehiculares
#   Backend: FastAPI + PostgreSQL (Supabase)
#   Universidad Autónoma Gabriel René Moreno - SI2 2026
#
# TABLAS QUE REPRESENTA ESTE ARCHIVO:
#   1. incidentes        → Flujo principal del sistema (CU7, CU10, CU11)
#   2. evidencias_ia     → Archivos multimodales del cliente para análisis (CU8)
#   3. historial_estados → Trazabilidad de cambios de estado (Auditoría)
#
# ACTORES QUE INTERACTÚAN:
#   A1 = Cliente (reporta la emergencia)
#   A2 = Taller (acepta/rechaza y asigna técnico)
#   A3 = Técnico (atiende el incidente en sitio)
#   A4 = Admin (supervisa todo el flujo)
# ============================================================

from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum as SAEnum, DECIMAL, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

# -------------------------------------------------------
# ENUMs - Estrictamente alineados con el Script de Supabase
# Evitan que entren datos basura a la base de datos
# -------------------------------------------------------
class EstadoIncidente(str, enum.Enum):
    pendiente  = "pendiente"
    en_proceso = "en proceso"
    atendido   = "atendido"

class PrioridadIncidente(str, enum.Enum):
    baja     = "baja"
    media    = "media"
    alta     = "alta"
    incierto = "incierto" # Valor por defecto hasta que la IA (CU8) lo clasifique

class TipoEvidencia(str, enum.Enum):
    audio  = "audio"
    imagen = "imagen"
    texto  = "texto"

# -------------------------------------------------------
# TABLA PRINCIPAL: incidentes
# Registro central de cada emergencia vehicular.
# -------------------------------------------------------
class Incidente(Base):
    __tablename__ = "incidentes"

    id_incidente             = Column(Integer, primary_key=True, index=True)
    cliente_id               = Column(Integer, ForeignKey("usuarios.id_usuario"))
    vehiculo_id              = Column(Integer, ForeignKey("vehiculos.id_vehiculo"))
    
    # El técnico es NULL al inicio. Se llena en el CU11 (Asignación)
    tecnico_id               = Column(Integer, ForeignKey("tecnicos.id_tecnico"), nullable=True)
    
    fecha_creacion_timestamp = Column(TIMESTAMP, server_default=func.now())
    estado_enum              = Column(SAEnum(EstadoIncidente, name="estado_incidente"), default=EstadoIncidente.pendiente)
    prioridad_enum           = Column(SAEnum(PrioridadIncidente, name="prioridad_incidente"), default=PrioridadIncidente.incierto)
    descripcion_texto        = Column(Text, nullable=True)
    
    # Coordenadas exactas mapeadas como DECIMAL(10,8) según el script BD
    latitud_emergencia       = Column(DECIMAL(10, 8))
    longitud_emergencia      = Column(DECIMAL(10, 8))

    # Relaciones ORM: cascade="all, delete" asegura limpieza en BD si se borra un incidente
    evidencias = relationship("EvidenciaIA", back_populates="incidente", cascade="all, delete")
    historial  = relationship("HistorialEstado", back_populates="incidente", cascade="all, delete")

# -------------------------------------------------------
# TABLA SECUNDARIA: evidencias_ia
# Guarda URLs de fotos/audios. La IA actualizará los
# campos de transcripción y clasificación posteriormente.
# -------------------------------------------------------
class EvidenciaIA(Base):
    __tablename__ = "evidencias_ia"

    id_evidencia              = Column(Integer, primary_key=True, index=True)
    incidente_id              = Column(Integer, ForeignKey("incidentes.id_incidente", ondelete="CASCADE"))
    tipo_enum                 = Column(SAEnum(TipoEvidencia, name="tipo_evidencia"), nullable=False)
    url_recurso               = Column(Text, nullable=False)
    transcripcion_audio_texto = Column(Text, nullable=True) # Resultado del ASR (OpenAI Whisper)
    clasificacion_ia_texto    = Column(String(100), nullable=True) # Diagnóstico generado
    nivel_confianza           = Column(DECIMAL(5, 2), nullable=True)

    incidente = relationship("Incidente", back_populates="evidencias")

# -------------------------------------------------------
# TABLA SECUNDARIA: historial_estados
# Garantiza la trazabilidad requerida en el sistema.
# Registra quién y cuándo cambió el estado de la emergencia.
# -------------------------------------------------------
class HistorialEstado(Base):
    __tablename__ = "historial_estados"

    id_historial         = Column(Integer, primary_key=True, index=True)
    incidente_id         = Column(Integer, ForeignKey("incidentes.id_incidente"))
    estado_enum          = Column(SAEnum(EstadoIncidente, name="estado_incidente"), nullable=False)
    fecha_hora_timestamp = Column(TIMESTAMP, server_default=func.now())
    comentario_texto     = Column(Text, nullable=True)

    incidente = relationship("Incidente", back_populates="historial")