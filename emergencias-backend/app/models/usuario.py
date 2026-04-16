# ============================================================
# models/usuario.py
# Representa la tabla "usuarios" de la base de datos
# SQLAlchemy mapea esta clase a la tabla real en Supabase
# ============================================================

from sqlalchemy import Column, Integer, String, Enum as SAEnum
from app.database import Base
import enum


# Enum igual al que definimos en la BD de Supabase
class TipoRol(str, enum.Enum):
    cliente    = "cliente"
    taller     = "taller"
    tecnico    = "tecnico"
    admin      = "admin"


class Usuario(Base):
    __tablename__ = "usuarios"

    id_usuario    = Column(Integer, primary_key=True, index=True)
    nombre        = Column(String(100), nullable=False)
    email         = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    telefono      = Column(String(20))
    rol           = Column(SAEnum(TipoRol, name="tipo_rol"), default=TipoRol.cliente)