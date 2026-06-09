from pydantic import BaseModel
from typing import Optional

class TenantBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None

class TenantCreate(TenantBase):
    pass

class TenantOut(TenantBase):
    id_tenant: int
    estado: str = "activo"

    class Config:
        from_attributes = True
