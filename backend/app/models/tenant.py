# ============================================================
# models/tenant.py
# Multi-tenant SaaS support
# ============================================================
from sqlalchemy import Column, Integer, String
from app.database import Base

class Tenant(Base):
    __tablename__ = "tenants"

    id_tenant   = Column(Integer, primary_key=True, index=True)
    nombre      = Column(String(100), unique=True, nullable=False)
    descripcion = Column(String(255), nullable=True)
    estado      = Column(String(20), default="activo", nullable=False)
