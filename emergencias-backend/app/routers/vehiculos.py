# ============================================================
# routers/vehiculos.py
#
# CU5: Administrar Vehículos
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.usuario import Usuario
from app.models.vehiculo import Vehiculo
from app.schemas.vehiculo import VehiculoCreate, VehiculoUpdate, VehiculoOut
from app.routers.auth import get_current_user

router = APIRouter(prefix="/vehiculos", tags=["CU5 - Administrar Vehículos"])

# -------------------------------------------------------
# POST /vehiculos/
# El cliente registra un nuevo auto. Se asocia a su ID.
# -------------------------------------------------------
@router.post("/", response_model=VehiculoOut, status_code=status.HTTP_201_CREATED)
def registrar_vehiculo(
    datos: VehiculoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Validar que la placa no exista en toda la plataforma
    existe_placa = db.query(Vehiculo).filter(Vehiculo.placa == datos.placa).first()
    if existe_placa:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Esta placa ya se encuentra registrada."
        )

    nuevo_vehiculo = Vehiculo(
        usuario_id = current_user.id_usuario, # <-- Se asigna al dueño logueado
        placa      = datos.placa,
        marca      = datos.marca,
        modelo     = datos.modelo,
        color      = datos.color
    )
    
    db.add(nuevo_vehiculo)
    db.commit()
    db.refresh(nuevo_vehiculo)
    return nuevo_vehiculo

# -------------------------------------------------------
# GET /vehiculos/
# Devuelve SOLO los vehículos del cliente autenticado
# -------------------------------------------------------
@router.get("/", response_model=List[VehiculoOut])
def listar_mis_vehiculos(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # El filtro garantiza la privacidad de los datos
    mis_vehiculos = db.query(Vehiculo).filter(Vehiculo.usuario_id == current_user.id_usuario).all()
    return mis_vehiculos

# -------------------------------------------------------
# GET /vehiculos/{id_vehiculo}
# -------------------------------------------------------
@router.get("/{id_vehiculo}", response_model=VehiculoOut)
def obtener_mi_vehiculo(
    id_vehiculo: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    vehiculo = db.query(Vehiculo).filter(
        Vehiculo.id_vehiculo == id_vehiculo,
        Vehiculo.usuario_id == current_user.id_usuario
    ).first()
    
    if not vehiculo:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado o no te pertenece.")
    return vehiculo

# -------------------------------------------------------
# PATCH /vehiculos/{id_vehiculo}
# -------------------------------------------------------
@router.patch("/{id_vehiculo}", response_model=VehiculoOut)
def actualizar_mi_vehiculo(
    id_vehiculo: int,
    datos: VehiculoUpdate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    vehiculo = db.query(Vehiculo).filter(
        Vehiculo.id_vehiculo == id_vehiculo,
        Vehiculo.usuario_id == current_user.id_usuario
    ).first()
    
    if not vehiculo:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado o no te pertenece.")

    # Si se intenta cambiar la placa, verificar que no choque con otra
    if datos.placa and datos.placa != vehiculo.placa:
        existe = db.query(Vehiculo).filter(Vehiculo.placa == datos.placa).first()
        if existe:
            raise HTTPException(status_code=400, detail="La nueva placa ya está en uso.")
        vehiculo.placa = datos.placa

    if datos.marca is not None:  vehiculo.marca = datos.marca
    if datos.modelo is not None: vehiculo.modelo = datos.modelo
    if datos.color is not None:  vehiculo.color = datos.color

    db.commit()
    db.refresh(vehiculo)
    return vehiculo

# -------------------------------------------------------
# DELETE /vehiculos/{id_vehiculo}
# -------------------------------------------------------
@router.delete("/{id_vehiculo}")
def eliminar_mi_vehiculo(
    id_vehiculo: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    vehiculo = db.query(Vehiculo).filter(
        Vehiculo.id_vehiculo == id_vehiculo,
        Vehiculo.usuario_id == current_user.id_usuario
    ).first()
    
    if not vehiculo:
        raise HTTPException(status_code=404, detail="Vehículo no encontrado o no te pertenece.")

    db.delete(vehiculo)
    db.commit()
    return {"message": "Vehículo eliminado correctamente"}