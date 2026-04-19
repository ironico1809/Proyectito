# ============================================================
# routers/pagos.py
# CASOS DE USO IMPLEMENTADOS AQUÍ:
#   - CU13: Gestión de Pagos de Servicio (Móvil)
#   - CU14: Administración de Comisiones (Web Admin)
# ============================================================
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.database import get_db
from app.models.pago import Pago
from app.models.incidente import Incidente, EstadoIncidente
from app.schemas.pago import PagoCreate, PagoOut

router = APIRouter(prefix="/pagos", tags=["Gestión Financiera (CU13, CU14)"])

# -------------------------------------------------------
# CU13: CLIENTE REALIZA EL PAGO DEL SERVICIO
# -------------------------------------------------------
@router.post("/", response_model=PagoOut, status_code=status.HTTP_201_CREATED)
def registrar_pago(datos: PagoCreate, db: Session = Depends(get_db)):
    # 1. Validar que el incidente exista y haya sido atendido
    incidente = db.query(Incidente).filter(Incidente.id_incidente == datos.incidente_id).first()
    if not incidente:
        raise HTTPException(status_code=404, detail="Incidente no encontrado.")
    
    if incidente.estado_enum != EstadoIncidente.atendido:
        raise HTTPException(status_code=400, detail="Solo se pueden pagar incidentes con estado 'atendido'.")

    # 2. Validar que no se pague dos veces
    pago_previo = db.query(Pago).filter(Pago.incidente_id == datos.incidente_id).first()
    if pago_previo:
        raise HTTPException(status_code=400, detail="Este servicio ya fue pagado.")

    # 3. Registrar el pago
    nuevo_pago = Pago(
        incidente_id=datos.incidente_id,
        monto_total_decimal=datos.monto_total_decimal,
        metodo_enum=datos.metodo_enum
    )
    
    db.add(nuevo_pago)
    db.commit()
    
    # 4. Refrescar para que Postgres nos devuelva el 10% calculado
    db.refresh(nuevo_pago) 
    
    return nuevo_pago

# -------------------------------------------------------
# CU14: REPORTES DE COMISIONES PARA EL ADMINISTRADOR
# -------------------------------------------------------
@router.get("/", response_model=List[PagoOut])
def listar_todos_los_pagos(db: Session = Depends(get_db)):
    """ Retorna todos los pagos y sus comisiones para el Dashboard del Admin """
    return db.query(Pago).all()

# -------------------------------------------------------
# MIS INGRESOS (Para el Taller)
# -------------------------------------------------------
@router.get("/taller/{taller_id}", response_model=List[PagoOut])
def listar_pagos_por_taller(taller_id: int, db: Session = Depends(get_db)):
    """ Devuelve solo los pagos de los servicios realizados por los técnicos de un taller específico """
    from app.models.tecnico import Tecnico # Importamos el modelo aquí para evitar dependencias circulares
    
    # Hacemos un JOIN: Pago -> Incidente -> Tecnico para filtrar por el Taller
    pagos = db.query(Pago)\
        .join(Incidente, Pago.incidente_id == Incidente.id_incidente)\
        .join(Tecnico, Incidente.tecnico_id == Tecnico.id_tecnico)\
        .filter(Tecnico.taller_id == taller_id).all()
        
    return pagos