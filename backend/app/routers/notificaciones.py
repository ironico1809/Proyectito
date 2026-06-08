# ============================================================
# routers/notificaciones.py
# CU15: Servicio de Notificaciones y Comunicación
#
# ENDPOINTS:
#   GET   /notificaciones/mis-notificaciones → Ver mis alertas
#   PATCH /notificaciones/{id}/leer          → Marcar como leída
#   GET   /notificaciones/no-leidas          → Contar no leídas (para badge)
#
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models.notificacion import Notificacion
from app.models.usuario import Usuario
from app.schemas.notificacion import NotificacionOut, MarcarLeida
from app.routers.auth import get_current_user

router = APIRouter(prefix="/notificaciones", tags=["CU15 - Notificaciones"])


# -------------------------------------------------------
# Función interna reutilizable
# La llaman otros routers (incidentes, etc.) para crear
# notificaciones automáticas sin pasar por HTTP
# -------------------------------------------------------
import firebase_admin
from firebase_admin import messaging

import threading

def _enviar_push_async(mensaje_push):
    try:
        messaging.send(mensaje_push)
    except Exception as e:
        print(f"Error al enviar notificación Push asíncrona: {e}")

def crear_notificacion_interna(db: Session, usuario_id: int, titulo: str, mensaje: str):
    notif = Notificacion(
        usuario_id = usuario_id,
        titulo     = titulo,
        mensaje    = mensaje
    )
    db.add(notif)
    
    # Intentar enviar notificación Push si el usuario tiene FCM Token
    usuario = db.query(Usuario).filter(Usuario.id_usuario == usuario_id).first()
    if usuario and getattr(usuario, "fcm_token", None):
        try:
            mensaje_push = messaging.Message(
                notification=messaging.Notification(
                    title=titulo,
                    body=mensaje,
                ),
                token=usuario.fcm_token,
            )
            threading.Thread(target=_enviar_push_async, args=(mensaje_push,)).start()
        except Exception as e:
            print(f"Error al armar notificación Push a usuario {usuario_id}: {e}")
    

# -------------------------------------------------------
# GET /notificaciones/mis-notificaciones
# Devuelve todas las notificaciones del usuario autenticado
# Ordenadas de más reciente a más antigua
# -------------------------------------------------------
@router.get("/mis-notificaciones", response_model=List[NotificacionOut])
def mis_notificaciones(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    return db.query(Notificacion).filter(
        Notificacion.usuario_id == current_user.id_usuario
    ).order_by(Notificacion.fecha_creacion_timestamp.desc()).all()


# -------------------------------------------------------
# GET /notificaciones/no-leidas
# Devuelve el conteo de notificaciones no leídas
# El frontend Angular lo usa para mostrar el badge en navbar
# -------------------------------------------------------
@router.get("/no-leidas")
def contar_no_leidas(
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    total = db.query(Notificacion).filter(
        Notificacion.usuario_id  == current_user.id_usuario,
        Notificacion.leido_boolean == False
    ).count()
    return {"total_no_leidas": total}


# -------------------------------------------------------
# PATCH /notificaciones/{id}/leer
# Marcar una notificación como leída
# El frontend llama esto cuando el usuario abre la alerta
# -------------------------------------------------------
@router.patch("/{id_notificacion}/leer", response_model=NotificacionOut)
def marcar_leida(
    id_notificacion: int,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    notif = db.query(Notificacion).filter(
        Notificacion.id_notificacion == id_notificacion,
        Notificacion.usuario_id      == current_user.id_usuario
    ).first()

    if not notif:
        raise HTTPException(status_code=404, detail="Notificación no encontrada")

    notif.leido_boolean = True
    db.commit()
    db.refresh(notif)
    return notif