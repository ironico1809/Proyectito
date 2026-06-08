from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import DATABASE_URL

# pool_pre_ping=True reconecta automáticamente si Supabase cierra la conexión
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,        # verifica la conexión antes de usarla
    pool_recycle=300,          # recicla conexiones cada 5 minutos
    pool_size=5,
    max_overflow=10
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()