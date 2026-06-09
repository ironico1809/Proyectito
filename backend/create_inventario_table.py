import os
import sys

backend_path = os.path.abspath(os.path.dirname(__file__))
sys.path.append(backend_path)

from app.database import Base, engine
# Import all models to register them in Base.metadata
from app.models.tenant import Tenant
from app.models.usuario import Usuario
from app.models.taller import Taller, TallerInventario
from app.models.tecnico import Tecnico
from app.models.vehiculo import Vehiculo
from app.models.incidente import Incidente, EvidenciaIA, HistorialEstado
from app.models.cotizacion import Cotizacion
from app.models.pago import Pago

print("Creating tables in database if they do not exist...")
try:
    Base.metadata.create_all(bind=engine)
    print("Successfully verified and created all missing tables in database!")
except Exception as e:
    print("Error creating tables:", e)
