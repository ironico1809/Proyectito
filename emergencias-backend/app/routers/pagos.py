from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.pago import Pago
from app.models.incidente import Incidente, EstadoIncidente
from app.models.taller import Taller
from app.models.usuario import Usuario
from app.routers.auth import get_current_user # Tu dependencia de JWT
from app.schemas.pago import PagoCreate, PagoOut

router = APIRouter(prefix="/pagos", tags=["Gestión Financiera"])

# 1. EL CLIENTE PAGA (Se asigna el dinero automáticamente al dueño del taller)
@router.post("/", response_model=PagoOut, status_code=status.HTTP_201_CREATED)
def registrar_pago(datos: PagoCreate, db: Session = Depends(get_db)):
    incidente = db.query(Incidente).filter(Incidente.id_incidente == datos.incidente_id).first()
    if not incidente or not incidente.taller_actual_id:
        raise HTTPException(status_code=400, detail="Incidente no válido o sin taller asignado.")

    taller = db.query(Taller).filter(Taller.id_taller == incidente.taller_actual_id).first()
    
    nuevo_pago = Pago(
        incidente_id=datos.incidente_id,
        dueño_taller_id=taller.dueño_id, # Magia: Se extrae el dueño del taller (ej. Antonio ID 3)
        monto_total_decimal=datos.monto_total_decimal,
        metodo_enum=datos.metodo_enum
    )
    db.add(nuevo_pago)
    db.commit()
    db.refresh(nuevo_pago) 
    return nuevo_pago

# 2. CU14: ADMIN VE TODA LA RECAUDACIÓN
@router.get("/", response_model=List[PagoOut])
def listar_todos_los_pagos(db: Session = Depends(get_db)):
    # Aquí puedes añadir verificación de rol para asegurar que solo el ADMIN entra
    return db.query(Pago).all()

# 3. CU13: EL DUEÑO DEL TALLER VE SUS PROPIOS INGRESOS
@router.get("/mis-ingresos", response_model=List[PagoOut])
def listar_mis_ingresos(db: Session = Depends(get_db), current_user: Usuario = Depends(get_current_user)):
    # Extrae el ID del token (current_user.id_usuario) y filtra
    return db.query(Pago).filter(Pago.dueño_taller_id == current_user.id_usuario).all()