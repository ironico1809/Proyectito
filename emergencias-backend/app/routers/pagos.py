from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.pago import Pago
from app.models.incidente import Incidente, EstadoIncidente
from app.models.taller import Taller
from app.models.usuario import Usuario
from app.routers.auth import get_current_user
from app.schemas.pago import PagoCreate, PagoOut
from app.utils.bitacora import registrar_evento  # CU21 — bitácora

router = APIRouter(prefix="/pagos", tags=["Gestión Financiera"])

# ===================================================================
# CU13: EL CLIENTE REGISTRA EL PAGO (PayPal ya procesó en el móvil)
# ===================================================================
@router.post("/", response_model=PagoOut, status_code=status.HTTP_201_CREATED)
def registrar_pago(
    datos: PagoCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    # Verificar que el incidente existe y tiene taller asignado
    incidente = db.query(Incidente).filter(Incidente.id_incidente == datos.incidente_id).first()
    if not incidente or not incidente.taller_actual_id:
        raise HTTPException(status_code=400, detail="Incidente no válido o sin taller asignado.")

    # Evitar pago duplicado para el mismo incidente
    pago_existente = db.query(Pago).filter(Pago.incidente_id == datos.incidente_id).first()
    if pago_existente:
        raise HTTPException(status_code=400, detail="Este incidente ya tiene un pago registrado.")

    taller = db.query(Taller).filter(Taller.id_taller == incidente.taller_actual_id).first()

    nuevo_pago = Pago(
        incidente_id=datos.incidente_id,
        dueño_taller_id=taller.dueño_id,  # El dinero va al dueño del taller
        monto_total_decimal=datos.monto_total_decimal,
        metodo_enum=datos.metodo_enum
    )
    db.add(nuevo_pago)

    # CU21 — registrar pago completado en bitácora
    registrar_evento(
        db, datos.incidente_id,
        "PAGO_COMPLETADO",
        f"Pago de {datos.monto_total_decimal} Bs. completado vía {datos.metodo_enum}.",
        current_user.id_usuario
    )

    db.commit()
    db.refresh(nuevo_pago)
    return nuevo_pago

# ===================================================================
# CU14: ADMIN VE TODA LA RECAUDACIÓN DE LA PLATAFORMA
# ===================================================================
@router.get("/", response_model=List[PagoOut])
def listar_todos_los_pagos(db: Session = Depends(get_db)):
    return db.query(Pago).all()

# ===================================================================
# CU13: EL DUEÑO DEL TALLER VE SUS PROPIOS INGRESOS
# ===================================================================
@router.get("/mis-ingresos", response_model=List[PagoOut])
def listar_mis_ingresos(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return db.query(Pago).filter(Pago.dueño_taller_id == current_user.id_usuario).all()