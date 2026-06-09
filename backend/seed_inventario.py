import os
import sys

backend_path = os.path.abspath(os.path.dirname(__file__))
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
    talleres = db.query(Taller).all()
    print(f"Encontrados {len(talleres)} talleres en la base de datos.")
    
    for t in talleres:
        # Check if already seeded
        existing = db.query(TallerInventario).filter(TallerInventario.taller_id == t.id_taller).first()
        if existing:
            print(f"El taller {t.nombre} ya tiene inventario. Saltando...")
            continue
            
        print(f"Sembrando inventario para taller: {t.nombre} (ID: {t.id_taller})")
        # 1. Llanta
        db.add(TallerInventario(taller_id=t.id_taller, item_nombre="llanta", cantidad=5))
        # 2. Batería
        db.add(TallerInventario(taller_id=t.id_taller, item_nombre="bateria", cantidad=3))
        # 3. Aceite
        db.add(TallerInventario(taller_id=t.id_taller, item_nombre="aceite", cantidad=10))
        
    db.commit()
    print("¡Inventario sembrado exitosamente!")
finally:
    db.close()
