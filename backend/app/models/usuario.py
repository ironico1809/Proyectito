# ============================================================
# models/usuario.py
from sqlalchemy import Column, Integer, String, Enum as SAEnum, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
import enum

class TipoRol(str, enum.Enum):
    cliente    = "cliente"
    taller     = "taller"
    tecnico    = "tecnico"
    admin      = "admin"
    superadmin = "superadmin"


class Usuario(Base):
    __tablename__ = "usuarios"

    id_usuario    = Column(Integer, primary_key=True, index=True)
    nombre        = Column(String(100), nullable=False)
    email         = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    telefono      = Column(String(20))
    rol           = Column(SAEnum(TipoRol, name="tipo_rol"), default=TipoRol.cliente)
    fcm_token     = Column(String(255), nullable=True)
    tenant_id     = Column(Integer, ForeignKey("tenants.id_tenant"), nullable=True, default=1)

    tenant        = relationship("Tenant", foreign_keys=[tenant_id])