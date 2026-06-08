# ============================================================
# schemas/vehiculo.py
#
# CU5: Administrar Vehículos
# ============================================================

from pydantic import BaseModel
from typing import Optional

# -------------------------------------------------------
# CU5 - REGISTRAR VEHÍCULO (Desde la App Móvil)
# -------------------------------------------------------
class VehiculoCreate(BaseModel):
    placa:  str
    marca:  Optional[str] = None
    modelo: Optional[str] = None
    color:  Optional[str] = None

# -------------------------------------------------------
# CU5 - ACTUALIZAR VEHÍCULO (Parcial)
# -------------------------------------------------------
class VehiculoUpdate(BaseModel):
    placa:  Optional[str] = None
    marca:  Optional[str] = None
    modelo: Optional[str] = None
    color:  Optional[str] = None

# -------------------------------------------------------
# CU5 - RESPUESTA VEHÍCULO
# -------------------------------------------------------
class VehiculoOut(BaseModel):
    id_vehiculo: int
    usuario_id:  int
    placa:       str
    marca:       Optional[str] = None
    modelo:      Optional[str] = None
    color:       Optional[str] = None

    class Config:
        from_attributes = True