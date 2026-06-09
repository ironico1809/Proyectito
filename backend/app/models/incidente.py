# ============================================================
# models/incidente.py
#
# CONTEXTO DEL PROYECTO:
#   Plataforma Inteligente de Emergencias Vehiculares
# TABLAS QUE REPRESENTA ESTE ARCHIVO:
#   1. incidentes        → Flujo principal del sistema (CU7, CU10, CU11)
#   2. evidencias_ia     → Archivos multimodales del cliente para análisis (CU8)
#   3. historial_estados → Trazabilidad de cambios de estado (Auditoría)
# ============================================================

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum as SAEnum, Numeric, TIMESTAMP, Text, DECIMAL
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base
import enum

# -------------------------------------------------------
# ENUMs - Estrictamente alineados con el Script de Supabase
# Evitan que entren datos basura a la base de datos
# -------------------------------------------------------
class EstadoIncidente(str, enum.Enum):
    # Estados originales (Ciclos 1-3)
    pendiente       = "pendiente"
    en_proceso      = "en_proceso"
    atendido        = "atendido"
    cancelado       = "cancelado"
    # Estados nuevos Ciclo 4 — CU17 WebSocket
    buscando_taller = "buscando_taller"
    taller_asignado = "taller_asignado"
    en_camino       = "en_camino"
    en_atencion     = "en_atencion"
    finalizado      = "finalizado"

class PrioridadIncidente(str, enum.Enum):
    baja     = "baja"
    media    = "media"
    alta     = "alta"
    incierto = "incierto" 

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
    
    taller_actual_id         = Column(Integer, ForeignKey("talleres.id_taller"), nullable=True)
    tecnico_id               = Column(Integer, ForeignKey("tecnicos.id_tecnico"), nullable=True)
    
    fecha_creacion_timestamp = Column(TIMESTAMP, server_default=func.now())
    estado_enum              = Column(SAEnum(EstadoIncidente, name="estado_incidente"), default=EstadoIncidente.pendiente)
    prioridad_enum           = Column(SAEnum(PrioridadIncidente, name="prioridad_incidente"), default=PrioridadIncidente.incierto)
    descripcion_texto        = Column(Text, nullable=True)
    costo_final_decimal = Column(DECIMAL(10, 2), nullable=True)
    latitud_emergencia       = Column(DECIMAL(12, 8))
    longitud_emergencia      = Column(DECIMAL(12, 8))
    latitud_tecnico  = Column(Numeric(10, 6), nullable=True)
    longitud_tecnico = Column(Numeric(10, 6), nullable=True)
    uuid_offline     = Column(String(36), unique=True, nullable=True)  # CU19 — deduplicación offline
    tenant_id                = Column(Integer, ForeignKey("tenants.id_tenant"), nullable=True, default=1)

    evidencias = relationship("EvidenciaIA", back_populates="incidente", cascade="all, delete")
    historial  = relationship("HistorialEstado", back_populates="incidente", cascade="all, delete")

    cliente = relationship("Usuario", foreign_keys=[cliente_id])
    vehiculo = relationship("Vehiculo", foreign_keys=[vehiculo_id])
    taller_actual = relationship("Taller", foreign_keys=[taller_actual_id])
    tecnico = relationship("Tecnico", foreign_keys=[tecnico_id])
    tenant = relationship("Tenant", foreign_keys=[tenant_id])

    @property
    def cliente_nombre(self):
        return self.cliente.nombre if self.cliente else None

    @property
    def vehiculo_placa(self):
        return self.vehiculo.placa if self.vehiculo else None

    @property
    def taller_nombre(self):
        return self.taller_actual.nombre if self.taller_actual else None

    @property
    def taller_telefono(self):
        if self.taller_actual and self.taller_actual.dueno:
            return self.taller_actual.dueno.telefono
        return None

    @property
    def tecnico_nombre(self):
        return self.tecnico.nombre if self.tecnico else None

    @property
    def tecnico_telefono(self):
        if self.tecnico and self.tecnico.usuario:
            return self.tecnico.usuario.telefono
        return None

    @property
    def tecnico_especialidad(self):
        return self.tecnico.especialidad if self.tecnico else None

    @property
    def clasificacion_ia(self):
        for ev in self.evidencias:
            if ev.clasificacion_ia_texto:
                return ev.clasificacion_ia_texto
        return "Sin procesar"

    @property
    def latitud_taller(self):
        return self.taller_actual.latitud_decimal if self.taller_actual else None

    @property
    def longitud_taller(self):
        return self.taller_actual.longitud_decimal if self.taller_actual else None


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