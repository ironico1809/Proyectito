# ============================================================
# main.py
#
# PUNTO DE ENTRADA DE LA APLICACIÓN
# Registra todos los routers por caso de uso:
#   - auth.py     → CU1: Autenticación
#   - usuarios.py → CU2: Gestión de Usuarios
#   - talleres.py → CU3: Gestión de Talleres  ← NUEVO

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import os
import firebase_admin
from firebase_admin import credentials

print(">>> INICIANDO APLICACIÓN <<<")
print(f"PORT ENV: {os.getenv('PORT')}")

firebase_key_path = os.path.join(os.path.dirname(__file__), "..", "firebase-adminsdk.json")
if os.path.exists(firebase_key_path) and not firebase_admin._apps:
    try:
        cred = credentials.Certificate(firebase_key_path)
        firebase_admin.initialize_app(cred)
        print("Firebase Admin SDK inicializado correctamente.")
    except Exception as e:
        print(f"Error al inicializar Firebase Admin: {e}")

from app.models import tenant
from app.models import bitacora
from app.models import taller_rechazo
from app.models import calificacion, consejo_vial  # Modelos nuevos - Ciclo 5 - CU23, CU25
from app.routers import auth, usuarios, talleres, vehiculos, tecnicos, incidentes, ia, notificaciones, pagos, websocket_incidente, cotizaciones, saas
from app.routers import bitacora as bitacora_router, kpis, calificaciones, reportes_ia, consejos_viales  # Routers - Ciclo 5
app = FastAPI(
    title="Plataforma Inteligente de Emergencias Vehiculares",
    description="API REST - Sistema de Información 2 | UAGRM Grupo 30", 
    version="1.0.0"
)

# -------------------------------------------------------
# CORS: permite que el Frontend consuma la API
# -------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
    allow_headers=["Content-Type", "Set-Cookie", "Authorization", "Access-Control-Allow-Origin", "Access-Control-Allow-Headers"],
)

# -------------------------------------------------------
# Registro de routers por caso de uso
# Cada router tiene su propio prefijo y tag en Swagger
# -------------------------------------------------------
app.include_router(auth.router)           # CU1 - /auth
app.include_router(usuarios.router)       # CU2 - /usuarios
app.include_router(talleres.router)       # CU3 - /talleres
app.include_router(vehiculos.router)      # CU5 - /vehiculos
app.include_router(tecnicos.router)       # CU6 - /tecnicos
app.include_router(incidentes.router)     # CU7, CU10, CU11 - /incidentes
app.include_router(ia.router)             # CU8 - /ia
app.include_router(notificaciones.router) # CU15 - /notificaciones
app.include_router(pagos.router)
app.include_router(websocket_incidente.router)
app.include_router(cotizaciones.router)
app.include_router(bitacora_router.router)    # CU21 - Bitácora de Trazabilidad - Ciclo 5
app.include_router(kpis.router)               # CU22 - Panel de KPIs - Ciclo 5
app.include_router(calificaciones.router)      # CU23 - Calificaciones Post-Servicio - Ciclo 5
app.include_router(reportes_ia.router)         # CU24 - Reportes Inteligentes IA - Ciclo 5
app.include_router(consejos_viales.router)     # CU25 - Consejos Seguridad Vial - Ciclo 5
app.include_router(saas.router)                # SaaS Operations

# -------------------------------------------------------
# Endpoint raíz: verifica que el servidor esté corriendo
# -------------------------------------------------------
@app.get("/")
def root():
    return {"message": "API de Emergencias Vehiculares corriendo ✓"}