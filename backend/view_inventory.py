import os
import sys

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..', '..', 'Documents', 'Proyecto', 'SI2_Examen_1', 'backend'))
sys.path.append(backend_path)

from app.database import SessionLocal
from app.models.tenant import Tenant
from app.models.usuario import Usuario
from app.models.taller import Taller, TallerInventario
from app.models.tecnico import Tecnico
from app.models.vehiculo import Vehiculo
from app.models.incidente import Incidente, EvidenciaIA, HistorialEstado
from app.models.cotizacion import Cotizacion
from app.models.pago import Pago

db = SessionLocal()
try:
    items = db.query(TallerInventario).all()
    print("=== INVENTARIO DE TALLERES EN LA BASE DE DATOS ===")
    if not items:
        print("No hay registros en la tabla taller_inventario.")
    for item in items:
        taller = db.query(Taller).filter(Taller.id_taller == item.taller_id).first()
        taller_nombre = taller.nombre if taller else "Taller Desconocido"
        print(f"Taller: {taller_nombre} (ID: {item.taller_id}) | Item: '{item.item_nombre}' | Cantidad: {item.cantidad}")
finally:
    db.close()
