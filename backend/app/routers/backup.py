# ============================================================
# routers/backup.py
# CU-BACKUP: Gestión de Copias de Seguridad
# ============================================================

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from sqlalchemy import text, inspect
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
import os
import json
import traceback

from app.database import get_db, engine
from app.models.backup import Backup, BackupConfig
from app.routers.auth import get_current_user

router = APIRouter(prefix="/backup", tags=["Backup & Mantenimiento"])

# Carpeta donde se guardan los archivos de backup
BACKUP_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "temp", "backups")
os.makedirs(BACKUP_DIR, exist_ok=True)


# -------------------------------------------------------
# Schemas
# -------------------------------------------------------
class BackupOut(BaseModel):
    id: int
    nombre_archivo: str
    tipo: str
    tamanio_bytes: Optional[int] = None
    creado_en: datetime

    class Config:
        from_attributes = True


class ConfigBackupIn(BaseModel):
    hora_automatico: Optional[str] = None
    automatico_activo: bool = False


class ConfigBackupOut(BaseModel):
    hora_automatico: Optional[str] = None
    automatico_activo: bool = False

    class Config:
        from_attributes = True


# -------------------------------------------------------
# Utilidad: exportar todas las tablas a JSON
# -------------------------------------------------------
def _serializar(val):
    """Convierte valores no serializables a string."""
    if isinstance(val, datetime):
        return val.isoformat()
    if isinstance(val, bytes):
        return val.hex()
    return val


def _exportar_tablas_a_json(db: Session) -> dict:
    """Lee TODAS las tablas de la BD y las devuelve como dict."""
    insp = inspect(engine)
    tabla_nombres = insp.get_table_names()
    datos = {}

    for tabla in tabla_nombres:
        try:
            columnas = [col["name"] for col in insp.get_columns(tabla)]
            resultado = db.execute(text(f'SELECT * FROM "{tabla}"'))
            filas = resultado.fetchall()
            datos[tabla] = [
                {col: _serializar(fila[i]) for i, col in enumerate(columnas)}
                for fila in filas
            ]
        except Exception as e:
            datos[tabla] = {"error": str(e)}

    return datos


# -------------------------------------------------------
# GET /backup/historial
# -------------------------------------------------------
@router.get("/historial", response_model=List[BackupOut])
def listar_backups(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return db.query(Backup).order_by(Backup.creado_en.desc()).all()


# -------------------------------------------------------
# POST /backup/generar
# -------------------------------------------------------
@router.post("/generar", response_model=BackupOut, status_code=status.HTTP_201_CREATED)
def generar_backup_manual(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        ahora = datetime.now()
        nombre = f"backup_{ahora.strftime('%Y-%m-%d_%H-%M-%S')}.json"
        ruta = os.path.join(BACKUP_DIR, nombre)

        # Exportar todas las tablas
        datos = _exportar_tablas_a_json(db)

        # Escribir archivo JSON
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(datos, f, ensure_ascii=False, indent=2, default=str)

        tamanio = os.path.getsize(ruta)

        # Guardar registro en BD
        registro = Backup(
            nombre_archivo=nombre,
            tipo="manual",
            tamanio_bytes=tamanio,
            ruta_archivo=ruta,
        )
        db.add(registro)
        db.commit()
        db.refresh(registro)

        return registro

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error al generar backup: {str(e)}"
        )


# -------------------------------------------------------
# GET /backup/descargar/{backup_id}
# -------------------------------------------------------
@router.get("/descargar/{backup_id}")
def descargar_backup(
    backup_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    backup = db.query(Backup).filter(Backup.id == backup_id).first()
    if not backup:
        raise HTTPException(status_code=404, detail="Backup no encontrado")

    if not backup.ruta_archivo or not os.path.exists(backup.ruta_archivo):
        raise HTTPException(
            status_code=404,
            detail="El archivo ya no está disponible en el servidor",
        )

    return FileResponse(
        path=backup.ruta_archivo,
        filename=backup.nombre_archivo,
        media_type="application/json",
    )


# -------------------------------------------------------
# DELETE /backup/{backup_id}
# -------------------------------------------------------
@router.delete("/{backup_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_backup(
    backup_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    backup = db.query(Backup).filter(Backup.id == backup_id).first()
    if not backup:
        raise HTTPException(status_code=404, detail="Backup no encontrado")

    if backup.ruta_archivo and os.path.exists(backup.ruta_archivo):
        os.remove(backup.ruta_archivo)

    db.delete(backup)
    db.commit()


# -------------------------------------------------------
# GET /backup/configuracion
# -------------------------------------------------------
@router.get("/configuracion", response_model=ConfigBackupOut)
def obtener_config(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        config = db.query(BackupConfig).first()
        if not config:
            config = BackupConfig(id=1, hora_automatico=None, automatico_activo=False)
            db.add(config)
            db.commit()
            db.refresh(config)
        return config
    except Exception:
        # Si la tabla no existe, devolver valores por defecto
        return ConfigBackupOut(hora_automatico=None, automatico_activo=False)


# -------------------------------------------------------
# POST /backup/configuracion
# -------------------------------------------------------
@router.post("/configuracion", response_model=ConfigBackupOut)
def guardar_config(
    datos: ConfigBackupIn,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        config = db.query(BackupConfig).first()
        if not config:
            config = BackupConfig(id=1)
            db.add(config)

        config.hora_automatico = datos.hora_automatico
        config.automatico_activo = datos.automatico_activo
        db.commit()
        db.refresh(config)
        return config
    except Exception as e:
        db.rollback()
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Error al guardar config: {str(e)}"
        )
    # -------------------------------------------------------
# Tarea en segundo plano: Planificador de Backup Automático
# -------------------------------------------------------
async def planificador_backup_automatico():
    import asyncio
    from app.database import SessionLocal
    
    print("⏰ Planificador de backups automáticos iniciado.")
    ultimo_ejecutado = None
    
    while True:
        try:
            await asyncio.sleep(30)  # Verifica la hora cada 30 segundos
            ahora = datetime.now()
            hora_actual_str = ahora.strftime("%H:%M")
            
            # Evita ejecutar múltiples veces en el mismo minuto
            if ultimo_ejecutado == hora_actual_str:
                continue
                
            db = SessionLocal()
            try:
                config = db.query(BackupConfig).first()
                # Si la automatización está activa y coincide la hora
                if config and config.automatico_activo and config.hora_automatico == hora_actual_str:
                    print(f"🚀 Iniciando backup automático para las {hora_actual_str}...")
                    
                    nombre = f"backup_auto_{ahora.strftime('%Y-%m-%d_%H-%M-%S')}.json"
                    ruta = os.path.join(BACKUP_DIR, nombre)
                    
                    datos = _exportar_tablas_a_json(db)
                    
                    with open(ruta, "w", encoding="utf-8") as f:
                        json.dump(datos, f, ensure_ascii=False, indent=2, default=str)
                        
                    tamanio = os.path.getsize(ruta)
                    
                    registro = Backup(
                        nombre_archivo=nombre,
                        tipo="automatico",
                        tamanio_bytes=tamanio,
                        ruta_archivo=ruta,
                    )
                    db.add(registro)
                    db.commit()
                    
                    print(f"✅ Backup automático '{nombre}' generado correctamente.")
                    ultimo_ejecutado = hora_actual_str
            finally:
                db.close()
        except Exception as e:
            print(f"❌ Error en planificador de backup: {e}")