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


import json


print(">>> INICIANDO APLICACIÓN <<<")
print(f"PORT ENV: {os.getenv('PORT')}")

firebase_creds_json = os.getenv("FIREBASE_CREDENTIALS")
firebase_key_path = os.path.join(os.path.dirname(__file__), "..", "firebase-adminsdk.json")

if not firebase_admin._apps:
    if firebase_creds_json:
        try:
            creds_dict = json.loads(firebase_creds_json)
            cred = credentials.Certificate(creds_dict)
            firebase_admin.initialize_app(cred)
            print("Firebase Admin SDK inicializado correctamente (desde env var).")
        except Exception as e:
            print(f"Error al inicializar Firebase Admin desde env var: {e}")
    elif os.path.exists(firebase_key_path):
        try:
            cred = credentials.Certificate(firebase_key_path)
            firebase_admin.initialize_app(cred)
            print("Firebase Admin SDK inicializado correctamente (desde archivo local).")
        except Exception as e:
            print(f"Error al inicializar Firebase Admin: {e}")


from app.models import tenant
from app.models import bitacora
from app.models import taller_rechazo
from app.models import calificacion, consejo_vial  # Modelos nuevos - Ciclo 5 - CU23, CU25
from app.models import backup  
from app.routers import auth, usuarios, talleres, vehiculos, tecnicos, incidentes, ia, notificaciones, pagos, websocket_incidente, cotizaciones, saas
from app.routers import bitacora as bitacora_router, kpis, calificaciones, reportes_ia, consejos_viales  # Routers - Ciclo 5
from app.routers import backup as backup_router 
app = FastAPI(
    title="Plataforma Inteligente de Emergencias Vehiculares",
    description="API REST - Sistema de Información 2 | UAGRM Grupo 30", 
    version="1.0.0"
)

# -------------------------------------------------------
# CORS: Configuración para Producción
# -------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/health")
def health_check():
    return {"status": "ok", "port": os.getenv("PORT")}

# -------------------------------------------------------
# Firebase Admin con seguridad contra fallos
# -------------------------------------------------------
if not firebase_admin._apps:
    firebase_creds_json = os.getenv("FIREBASE_CREDENTIALS")
    firebase_key_path = os.path.join(os.path.dirname(__file__), "..", "firebase-adminsdk.json")
    if firebase_creds_json:
        try:
            import json
            creds_dict = json.loads(firebase_creds_json)
            cred = credentials.Certificate(creds_dict)
            firebase_admin.initialize_app(cred)
            print("✅ Firebase Admin listo (desde env var).")
        except Exception as e:
            print(f"❌ Error Firebase desde env var: {e}")
    elif os.path.exists(firebase_key_path):
        try:
            cred = credentials.Certificate(firebase_key_path)
            firebase_admin.initialize_app(cred)
            print("✅ Firebase Admin listo (desde archivo local).")
        except Exception as e:
            print(f"❌ Error Firebase: {e}")
    else:
        print("⚠️ Advertencia: firebase-adminsdk.json no encontrado y FIREBASE_CREDENTIALS vacío. Notificaciones push desactivadas.")

# -------------------------------------------------------
# Registro de routers por caso de uso
# -------------------------------------------------------
app.include_router(auth.router)
app.include_router(usuarios.router)
app.include_router(talleres.router)
app.include_router(vehiculos.router)
app.include_router(tecnicos.router)
app.include_router(incidentes.router)
app.include_router(ia.router)
app.include_router(notificaciones.router)
app.include_router(pagos.router)
app.include_router(websocket_incidente.router)
app.include_router(cotizaciones.router)
app.include_router(bitacora_router.router)
app.include_router(kpis.router)
app.include_router(calificaciones.router)
app.include_router(reportes_ia.router)
app.include_router(consejos_viales.router)
app.include_router(saas.router)
app.include_router(backup_router.router)

@app.get("/")
def root():
    return {"message": "API de Emergencias Vehiculares corriendo ✓"}
@app.on_event("startup")
async def startup_event():
    import asyncio
    from app.routers.backup import planificador_backup_automatico
    # Ejecuta el planificador en segundo plano
    asyncio.create_task(planificador_backup_automatico())