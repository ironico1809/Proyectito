from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import stripe
from app.database import get_db
from app.models.pago import Pago
from app.models.incidente import Incidente, EstadoIncidente
from app.models.taller import Taller
from app.models.usuario import Usuario
from app.routers.auth import get_current_user
from app.schemas.pago import PagoCreate, PagoOut, StripeIntentCreate, StripeIntentOut
from app.utils.bitacora import registrar_evento  # CU21 — bitácora

stripe.api_key = "sk_test_51SST3pGRwb0l2ATk8BzWCnkYyAeSqK9e7XrlQFMRBjW48uozcCcww6GDbqhi1kLHTmIkVEAgQPX8H1pxQnwKwiDK00QposqiTb"

# ===================================================================
# IDEA 3: SCHEDULER PARA MANTENIMIENTO PREVENTIVO
# ===================================================================
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from app.routers.notificaciones import crear_notificacion_interna
from app.database import SessionLocal

scheduler_mantenimiento = BackgroundScheduler()
scheduler_mantenimiento.start()

def disparar_campana_mantenimiento(cliente_id: int, taller_nombre: str):
    db = SessionLocal()
    try:
        crear_notificacion_interna(
            db, cliente_id,
            "🎁 ¡Regalo de TallerPro!",
            f"Hace poco visitaste {taller_nombre}. ¡Pasa hoy por una revisión con 10% de descuento!"
        )
    finally:
        db.close()

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

    # Notificar al dueño del taller del pago recibido
    crear_notificacion_interna(
        db, taller.dueño_id,
        "💰 Pago Recibido",
        f"Se ha registrado un pago de Bs. {datos.monto_total_decimal} para el incidente #{datos.incidente_id} vía {datos.metodo_enum}."
    )

    # CU21 — registrar pago completado en bitácora
    registrar_evento(
        db, datos.incidente_id,
        "PAGO_COMPLETADO",
        f"Pago de {datos.monto_total_decimal} Bs. completado vía {datos.metodo_enum}.",
        current_user.id_usuario
    )

    # =========================================================
    # IDEA 3: Programar Campaña de Mantenimiento Automático
    # =========================================================
    # Programamos a 30 días en la vida real. Aquí lo dejamos en 1 minuto
    # para que puedas ver la demostración y probar que sí llega la push.
    run_date = datetime.now() + timedelta(minutes=1)
    scheduler_mantenimiento.add_job(
        disparar_campana_mantenimiento,
        'date',
        run_date=run_date,
        args=[incidente.cliente_id, taller.nombre]
    )

    db.commit()
    db.refresh(nuevo_pago)
    return nuevo_pago

# ===================================================================
# CU14: ADMIN VE TODA LA RECAUDACIÓN DE LA PLATAFORMA
# ===================================================================
@router.get("/", response_model=List[PagoOut])
def listar_todos_los_pagos(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    query = db.query(Pago)
    if current_user.tenant_id is not None:
        query = query.join(Incidente).filter(Incidente.tenant_id == current_user.tenant_id)
    return query.all()

# ===================================================================
# CU13: EL DUEÑO DEL TALLER VE SUS PROPIOS INGRESOS
# ===================================================================
@router.get("/mis-ingresos", response_model=List[PagoOut])
def listar_mis_ingresos(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return db.query(Pago).filter(Pago.dueño_taller_id == current_user.id_usuario).all()

# ===================================================================
# CU13: EL CLIENTE VE SU HISTORIAL DE PAGOS
# ===================================================================
@router.get("/historial/cliente", response_model=List[PagoOut])
def listar_historial_pagos_cliente(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return db.query(Pago).join(Incidente).filter(Incidente.cliente_id == current_user.id_usuario).all()


# ===================================================================
# PASARELA DE PAGO: STRIPE CREAR INTENT
# ===================================================================
@router.post("/stripe/crear-intent", response_model=StripeIntentOut)
def crear_payment_intent(
    datos: StripeIntentCreate,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Crea un PaymentIntent en Stripe convirtiendo el monto en BOB a USD (TC: 6.96)."""
    incidente = db.query(Incidente).filter(Incidente.id_incidente == datos.incidente_id).first()
    if not incidente:
        raise HTTPException(status_code=404, detail="Incidente no encontrado.")

    # El costo final de la emergencia (usar un fallback si es nulo)
    monto_bob = float(incidente.costo_final_decimal) if incidente.costo_final_decimal else 100.0
    
    # Convertir a USD (tipo de cambio 6.96)
    monto_usd = monto_bob / 6.96
    
    # Convertir a centavos de dólar
    monto_centavos = int(round(monto_usd * 100))
    if monto_centavos < 50:  # Stripe exige un mínimo de 50 centavos de USD
        monto_centavos = 50

    try:
        intent = stripe.PaymentIntent.create(
            amount=monto_centavos,
            currency="usd",
            metadata={
                "incidente_id": incidente.id_incidente,
                "cliente_id": incidente.cliente_id,
                "monto_bob": str(monto_bob)
            }
        )
        return {
            "client_secret": intent.client_secret,
            "id_intent": intent.id
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error al crear el PaymentIntent en Stripe: {str(e)}"
        )

# ===================================================================
# IDEA 1: GENERADOR DE FACTURA PDF
# ===================================================================
from fastapi.responses import FileResponse
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
import os
import time

from fastapi import Query
from app.utils.security import decode_access_token

@router.get("/incidente/{id_incidente}/factura")
def descargar_factura(
    id_incidente: int,
    token: str = Query(None),
    db: Session = Depends(get_db)
):
    if not token:
        raise HTTPException(status_code=401, detail="No autenticado")
    
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Token inválido")

    # Verificar que el pago existe para este incidente
    pago = db.query(Pago).filter(Pago.incidente_id == id_incidente).first()
    if not pago:
        raise HTTPException(status_code=404, detail="No hay pago registrado para este incidente.")

    incidente = db.query(Incidente).filter(Incidente.id_incidente == id_incidente).first()
    cliente = db.query(Usuario).filter(Usuario.id_usuario == incidente.cliente_id).first()
    taller = db.query(Taller).filter(Taller.id_taller == incidente.taller_actual_id).first()
    vehiculo = db.query(Vehiculo).filter(Vehiculo.id_vehiculo == incidente.vehiculo_id).first()

    # Generar el PDF
    nombre_archivo = f"factura_incidente_{id_incidente}_{int(time.time())}.pdf"
    ruta_pdf = os.path.join("temp", nombre_archivo)
    os.makedirs("temp", exist_ok=True)

    c = canvas.Canvas(ruta_pdf, pagesize=letter)
    
    # --- HEADER / LOGO AREA ---
    c.setFillColorRGB(0.06, 0.09, 0.16) # Slate 900
    c.rect(0, 720, 612, 80, fill=1, stroke=0)
    c.setStrokeColorRGB(0.96, 0.62, 0.04) # Amber 500
    c.setLineWidth(3)
    c.line(0, 720, 612, 720)
    
    c.setFillColorRGB(1, 1, 1)
    c.setFont("Helvetica-Bold", 24)
    c.drawString(50, 750, "TALLERPRO")
    c.setFont("Helvetica", 10)
    c.drawString(50, 735, "RED NACIONAL DE AUXILIO MECÁNICO INTELIGENTE")
    
    c.setFont("Helvetica-Bold", 18)
    c.drawRightString(560, 750, "FACTURA / COMPROBANTE")
    c.setFont("Helvetica", 10)
    c.drawRightString(560, 735, f"Orden de Servicio #{id_incidente}")

    # --- INFORMACION GENERAL ---
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, 680, "FECHA DE EMISIÓN:")
    c.setFont("Helvetica", 12)
    c.drawString(180, 680, pago.fecha_pago_timestamp.strftime('%d/%m/%Y %H:%M'))

    c.setFont("Helvetica-Bold", 12)
    c.drawString(320, 680, "ESTADO DEL PAGO:")
    c.setFont("Helvetica-Bold", 12)
    estado_pago = pago.estado_pago_enum.upper() if hasattr(pago.estado_pago_enum, 'value') else str(pago.estado_pago_enum).upper()
    if "COMPLETADO" in estado_pago or "SUCCESS" in estado_pago:
        c.setFillColorRGB(0.06, 0.45, 0.31) # Success Green
    else:
        c.setFillColorRGB(0.93, 0.26, 0.26) # Danger Red
    c.drawString(450, 680, estado_pago)
    c.setFillColorRGB(0, 0, 0)

    # --- BOXES PARA CLIENTE Y TALLER ---
    # Background boxes
    c.setFillColorRGB(0.95, 0.96, 0.98)
    c.rect(50, 560, 240, 100, fill=1, stroke=0) # Cliente
    c.rect(320, 560, 240, 100, fill=1, stroke=0) # Taller
    
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 11)
    c.drawString(60, 645, "DATOS DEL CLIENTE")
    c.setFont("Helvetica", 10)
    c.drawString(60, 625, f"Nombre: {cliente.nombre if cliente else 'N/A'}")
    c.drawString(60, 610, f"Email: {cliente.email if cliente else 'N/A'}")
    c.drawString(60, 595, f"Teléfono: {cliente.telefono if hasattr(cliente, 'telefono') and cliente.telefono else 'S/N'}")
    
    c.setFont("Helvetica-Bold", 11)
    c.drawString(330, 645, "DATOS DEL TALLER")
    c.setFont("Helvetica", 10)
    c.drawString(330, 625, f"Taller: {taller.nombre if taller else 'N/A'}")
    c.drawString(330, 610, f"NIT/ID: {taller.nit if taller else 'S/N'}")
    c.drawString(330, 595, f"Dirección: {taller.direccion[:30] if hasattr(taller, 'direccion') and taller.direccion else 'S/N'}...")

    # --- DETALLES DEL VEHÍCULO ---
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, 530, "INFORMACIÓN DEL VEHÍCULO")
    c.line(50, 525, 560, 525)
    c.setFont("Helvetica", 11)
    if vehiculo:
        c.drawString(50, 505, f"Placa: {vehiculo.placa}")
        c.drawString(180, 505, f"Marca: {vehiculo.marca}")
        c.drawString(320, 505, f"Modelo: {vehiculo.modelo}")
        c.drawString(460, 505, f"Color: {vehiculo.color if hasattr(vehiculo, 'color') else 'N/A'}")
    else:
        c.drawString(50, 505, "Datos del vehículo no disponibles")

    # --- DETALLE DE CARGOS (TABLA) ---
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, 460, "DETALLE DEL SERVICIO")
    
    # Header de Tabla
    c.setFillColorRGB(0.9, 0.9, 0.9)
    c.rect(50, 435, 510, 20, fill=1, stroke=1)
    c.setFillColorRGB(0, 0, 0)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(60, 442, "DESCRIPCIÓN")
    c.drawRightString(550, 442, "SUBTOTAL (BS.)")
    
    # Contenido de Tabla
    c.setFont("Helvetica", 10)
    desc_corta = str(incidente.descripcion_texto)[:75] if incidente.descripcion_texto else "Servicio de auxilio mecánico general"
    c.drawString(60, 420, desc_corta)
    c.drawRightString(550, 420, f"{pago.monto_total_decimal:.2f}")
    
    # Totales
    c.line(350, 400, 560, 400)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(350, 380, "MONTO TOTAL:")
    c.drawRightString(550, 380, f"{pago.monto_total_decimal:.2f} Bs.")
    
    c.setFont("Helvetica", 9)
    c.setAlpha(0.6)
    c.drawString(350, 365, "Incluye impuestos de ley y comisión")
    c.setAlpha(1)

    # --- ANÁLISIS IA (VALOR AGREGADO) ---
    if incidente.clasificacion_ia:
        c.setDash(3, 3)
        c.roundRect(50, 280, 510, 60, 8, stroke=1, fill=0)
        c.setDash(1, 0)
        c.setFont("Helvetica-BoldOblique", 10)
        c.drawString(65, 325, "ANÁLISIS INTELIGENTE (IA):")
        c.setFont("Helvetica-Oblique", 9)
        # Dividir texto IA en dos líneas si es muy largo
        txt_ia = incidente.clasificacion_ia
        if len(txt_ia) > 90:
            c.drawString(65, 310, txt_ia[:90])
            c.drawString(65, 295, txt_ia[90:180])
        else:
            c.drawString(65, 310, txt_ia)

    # --- FOOTER / SEGURIDAD ---
    c.setFillColorRGB(0.4, 0.4, 0.4)
    c.setFont("Helvetica", 8)
    c.drawCentredString(306, 120, "Este documento es un comprobante fiscal válido emitido por TallerPro SaaS.")
    c.drawCentredString(306, 108, f"ID de Transacción: {pago.id_pago} | Token Verificación: {pago.incidente_id}-{int(time.time())}")
    
    # QR Placeholder (Simulado con un cuadro)
    c.setStrokeColorRGB(0, 0, 0)
    c.rect(275, 40, 60, 60, stroke=1, fill=0)
    c.setFont("Helvetica-Bold", 7)
    c.drawCentredString(306, 30, "VALIDACIÓN DIGITAL")

    c.save()

    return FileResponse(path=ruta_pdf, filename=nombre_archivo, media_type='application/pdf')