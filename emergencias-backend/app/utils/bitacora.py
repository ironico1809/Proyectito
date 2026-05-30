# ============================================================
# HELPER — Registrar evento en la bitácora
# Se importa desde cualquier router que cambie el estado
# Uso: registrar_evento(db, incidente_id, "TALLER_ACEPTO",
#                       "El taller aceptó la solicitud", usuario_id)
# ============================================================
from sqlalchemy.orm import Session
from app.models.bitacora import BitacoraIncidente

def registrar_evento(
    db: Session,
    incidente_id: int,
    evento: str,
    descripcion: str = "",
    usuario_id: int = None
):
    """
    Inserta un evento en la bitácora del incidente.
    NO hace commit — el commit lo hace el router que llama a esta función.
    """
    entrada = BitacoraIncidente(
        incidente_id=incidente_id,
        evento=evento,
        descripcion=descripcion,
        usuario_id=usuario_id
    )
    db.add(entrada)