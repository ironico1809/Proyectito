# ============================================================
# schemas/notificacion.py
#
# CONTEXTO DEL PROYECTO:
#   Plataforma Inteligente de Emergencias Vehiculares
#
# CU15: Servicio de Notificaciones y Comunicación
#
# NOTA PARA FRONTEND ANGULAR:
#   El navbar debe mostrar un ícono de campana con badge
#   indicando cuántas notificaciones hay sin leer.
#   Llamar GET /notificaciones/mis-notificaciones al cargar
#   la app y marcar como leídas con PATCH cuando el usuario
#   abre el panel de notificaciones
# ============================================================

from pydantic import BaseModel
from typing import Optional
from datetime import datetime


# Respuesta de una notificación individual
class NotificacionOut(BaseModel):
    id_notificacion:          int
    titulo:                   str
    mensaje:                  str
    leido_boolean:            bool
    fecha_creacion_timestamp: datetime

    class Config:
        from_attributes = True


# Para marcar notificación como leída
class MarcarLeida(BaseModel):
    leido_boolean: bool = True