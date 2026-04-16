# ============================================================
# database.py
# Configura la conexión a PostgreSQL usando SQLAlchemy
# Todos los archivos que necesiten la BD importan desde aquí
# ============================================================

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import DATABASE_URL

# Motor de conexión a la base de datos
engine = create_engine(DATABASE_URL)

# Fábrica de sesiones: cada request abre y cierra su propia sesión
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Clase base de la que heredan todos los modelos
Base = declarative_base()


# -------------------------------------------------------
# Dependencia para inyectar la sesión en cada endpoint
# Se usa con "Depends(get_db)" en los routers
# -------------------------------------------------------
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()