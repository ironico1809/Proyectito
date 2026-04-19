# ============================================================
# schemas/tecnico.py
#
# CONTEXTO DEL PROYECTO:
#   Plataforma Inteligente de Emergencias Vehiculares
#
# CU6: Administrar Staff Técnico (CRUD)
#   Actor: A2 (Taller)
#
# NOTA PARA FRONTEND ANGULAR:
#   La pantalla de gestión de técnicos muestra una tabla
#   con columnas: Nombre, Especialidad, Disponible (toggle)
#   El campo disponible_boolean se puede cambiar con PATCH
#   sin necesidad de editar todos los campos
# ============================================================

from pydantic import BaseModel, EmailStr
from typing import Optional

class TecnicoCreate(BaseModel):
    taller_id: int
    nombre: str          # Va a la tabla Usuario
    email: EmailStr      # Va a la tabla Usuario (Login)
    password: str        # Va a la tabla Usuario (Hash)
    telefono: Optional[str] = None
    especialidad: Optional[str] = None
    disponible_boolean: bool = True

class TecnicoUpdate(BaseModel):
    nombre: Optional[str] = None
    especialidad: Optional[str] = None
    disponible_boolean: Optional[bool] = None

class TecnicoPartial(BaseModel):
    nombre: Optional[str] = None
    especialidad: Optional[str] = None
    disponible_boolean: Optional[bool] = None

    class Config:
        from_attributes = True

class TecnicoOut(BaseModel):
    id_tecnico: int
    taller_id: int
    usuario_id: int
    nombre: str          # Se saca del join con Usuario
    especialidad: Optional[str] = None
    disponible_boolean: bool

    class Config:
        from_attributes = True