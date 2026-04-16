# ============================================================
# config.py
# Lee las variables del archivo .env y las expone al proyecto
# ============================================================

from dotenv import load_dotenv
import os

load_dotenv()

# URL de conexión a la base de datos en Supabase
DATABASE_URL = os.getenv("DATABASE_URL")

# Configuración para generar tokens JWT
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM", "HS256")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", 60))