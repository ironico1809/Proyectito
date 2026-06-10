# ============================================================
# models/backup.py
# Registro de Copias de Seguridad - ISO 25010
# ============================================================
from sqlalchemy import Column, Integer, String, Boolean, DateTime, func
from app.database import Base


class Backup(Base):
    __tablename__ = "backups"

    id              = Column(Integer, primary_key=True, index=True)
    nombre_archivo  = Column(String, nullable=False)
    tipo            = Column(String, default="manual")       # "manual" | "automatico"
    tamanio_bytes   = Column(Integer, nullable=True)
    ruta_archivo    = Column(String, nullable=True)
    creado_en       = Column(DateTime(timezone=True), server_default=func.now())


class BackupConfig(Base):
    __tablename__ = "backup_config"

    id                  = Column(Integer, primary_key=True, default=1)
    hora_automatico     = Column(String, nullable=True)      # "HH:MM"
    automatico_activo   = Column(Boolean, default=False)