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
from app.models import bitacora
from app.routers import auth, usuarios, talleres, vehiculos, tecnicos, incidentes, ia, notificaciones, pagos, websocket_incidente, cotizaciones
app = FastAPI(
    title="Plataforma Inteligente de Emergencias Vehiculares",
    description="API REST - Sistema de Información 2 | UAGRM Grupo 25", # <-- Decía Grupo 25
    version="1.0.0"
)

# -------------------------------------------------------
# CORS: permite que Angular (localhost:4200) consuma la API
# En producción reemplazar con el dominio real
# -------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
# -------------------------------------------------------
# Endpoint raíz: verifica que el servidor esté corriendo
# -------------------------------------------------------
@app.get("/")
def root():
    return {"message": "API de Emergencias Vehiculares corriendo ✓"}