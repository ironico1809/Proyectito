# ============================================================
# Router de Reportes Inteligentes por Voz y Texto - Ciclo 5 - CU24
# Genera reportes ejecutivos usando Groq IA con datos reales de la BD
# ============================================================

import os
import io
import json
import base64
import requests
import pandas as pd
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import func

HAS_MATPLOTLIB = False
try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    HAS_MATPLOTLIB = True
except Exception as e:
    print(f"Advertencia: Matplotlib no pudo cargarse ({e}). Los reportes PDF no tendrán gráficas.")

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

from app.database import get_db
from app.models.usuario import Usuario, TipoRol
from app.models.incidente import Incidente, EstadoIncidente, PrioridadIncidente
from app.models.pago import Pago
from app.models.taller import Taller
from app.models.tecnico import Tecnico
from app.models.excepcion import ExcepcionOperativa
from app.routers.auth import get_current_user
from app.schemas.reporte_ia import ReporteRequest, ReporteVozRequest, ReporteResponse

# Importar calificaciones si existe - Ciclo 5 - CU24
try:
    from app.models.calificacion import Calificacion
except ImportError:
    Calificacion = None

router = APIRouter(prefix="/reportes-ia", tags=["CU24 - Reportes Inteligentes IA"])

# API Key de Groq (misma que usa el proyecto) - Ciclo 5 - CU24
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")


def _recopilar_datos_periodo(db: Session, periodo_dias: int, user: Usuario) -> dict:
    """Recopila métricas reales de la BD para el periodo especificado con aislamiento SaaS"""
    fecha_inicio = datetime.now() - timedelta(days=periodo_dias)

    # Determinar filtro por taller si no es admin
    taller = None
    if user.rol != TipoRol.admin:
        taller = db.query(Taller).filter(Taller.dueño_id == user.id_usuario).first()

    # Incidentes del periodo con aislamiento tenant_id
    q_inc = db.query(Incidente).filter(Incidente.fecha_creacion_timestamp >= fecha_inicio)
    if user.tenant_id is not None:
        q_inc = q_inc.filter(Incidente.tenant_id == user.tenant_id)
    if taller:
        q_inc = q_inc.filter(Incidente.taller_actual_id == taller.id_taller)

    total_incidentes = q_inc.count()
    
    # Distribución por Estado
    estados_data = db.query(Incidente.estado_enum, func.count(Incidente.id_incidente))\
        .filter(Incidente.fecha_creacion_timestamp >= fecha_inicio)
    if user.tenant_id is not None:
        estados_data = estados_data.filter(Incidente.tenant_id == user.tenant_id)
    if taller:
        estados_data = estados_data.filter(Incidente.taller_actual_id == taller.id_taller)
    estados_dist = dict(estados_data.group_by(Incidente.estado_enum).all())
    
    # Distribución por Prioridad
    prio_data = db.query(Incidente.prioridad_enum, func.count(Incidente.id_incidente))\
        .filter(Incidente.fecha_creacion_timestamp >= fecha_inicio)
    if user.tenant_id is not None:
        prio_data = prio_data.filter(Incidente.tenant_id == user.tenant_id)
    if taller:
        prio_data = prio_data.filter(Incidente.taller_actual_id == taller.id_taller)
    prio_dist = dict(prio_data.group_by(Incidente.prioridad_enum).all())

    # Pagos del periodo
    q_pagos = db.query(Pago).filter(Pago.fecha_pago_timestamp >= fecha_inicio)
    if user.tenant_id is not None:
        q_pagos = q_pagos.join(Incidente).filter(Incidente.tenant_id == user.tenant_id)
    if taller:
        q_pagos = q_pagos.filter(Pago.dueño_taller_id == user.id_usuario)
    ingresos = float(q_pagos.with_entities(func.coalesce(func.sum(Pago.monto_total_decimal), 0)).scalar())
    total_pagos = q_pagos.count()

    # Top talleres
    top_talleres = []
    if user.rol == TipoRol.admin:
        query_talleres = db.query(Taller)
        if user.tenant_id is not None:
            query_talleres = query_talleres.filter(Taller.tenant_id == user.tenant_id)
        talleres_all = query_talleres.all()
        for t in talleres_all:
            q_inc_taller = db.query(Incidente).filter(
                Incidente.taller_actual_id == t.id_taller,
                Incidente.estado_enum.in_([EstadoIncidente.atendido, EstadoIncidente.finalizado]),
                Incidente.fecha_creacion_timestamp >= fecha_inicio
            )
            if user.tenant_id is not None:
                q_inc_taller = q_inc_taller.filter(Incidente.tenant_id == user.tenant_id)
            count = q_inc_taller.count()
            if count > 0:
                top_talleres.append({"nombre": t.nombre, "servicios": count})
        top_talleres.sort(key=lambda x: x["servicios"], reverse=True)
        top_talleres = top_talleres[:5]

    # Calificación promedio
    calif_promedio = 0.0
    if Calificacion is not None:
        q_calif = db.query(func.avg(Calificacion.puntuacion))
        if user.tenant_id is not None:
            q_calif = q_calif.join(Taller).filter(Taller.tenant_id == user.tenant_id)
        if taller:
            q_calif = q_calif.filter(Calificacion.taller_id == taller.id_taller)
        avg_val = q_calif.scalar()
        calif_promedio = round(float(avg_val), 1) if avg_val else 0.0

    # Incidentes por Mes (últimos 6 meses)
    incidentes_mes = []
    for i in range(5, -1, -1):
        target_date = datetime.now() - timedelta(days=i*30)
        mes_nombre = target_date.strftime("%b")
        inicio_mes = target_date.replace(day=1, hour=0, minute=0, second=0)
        fin_mes = (inicio_mes + timedelta(days=32)).replace(day=1)
        
        q_mes = db.query(Incidente).filter(Incidente.fecha_creacion_timestamp >= inicio_mes, Incidente.fecha_creacion_timestamp < fin_mes)
        if user.tenant_id is not None:
            q_mes = q_mes.filter(Incidente.tenant_id == user.tenant_id)
        if taller:
            q_mes = q_mes.filter(Incidente.taller_actual_id == taller.id_taller)
        
        incidentes_mes.append({"mes": mes_nombre, "total": q_mes.count()})

    return {
        "periodo_dias": periodo_dias,
        "fecha_inicio": fecha_inicio.strftime("%Y-%m-%d"),
        "fecha_fin": datetime.now().strftime("%Y-%m-%d"),
        "total_incidentes": total_incidentes,
        "estados_dist": {str(k.value): v for k, v in estados_dist.items()},
        "prio_dist": {str(k.value): v for k, v in prio_dist.items()},
        "incidentes_mes": incidentes_mes,
        "tasa_exito": round((estados_dist.get(EstadoIncidente.finalizado, 0) + estados_dist.get(EstadoIncidente.atendido, 0)) / total_incidentes * 100, 1) if total_incidentes > 0 else 0,
        "ingresos_totales_bs": ingresos,
        "total_pagos": total_pagos,
        "calificacion_promedio": calif_promedio,
        "top_talleres": top_talleres,
        "tenant_id": user.tenant_id
    }


def _generar_grafica_matplotlib(datos: list, etiquetas: list, titulo: str, tipo: str = 'bar') -> io.BytesIO:
    """Genera una gráfica con matplotlib y devuelve un buffer de bytes"""
    plt.figure(figsize=(6, 4))
    if tipo == 'bar':
        plt.bar(etiquetas, datos, color=['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'])
        plt.ylabel('Cantidad')
    elif tipo == 'pie':
        plt.pie(datos, labels=etiquetas, autopct='%1.1f%%', colors=['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#06b6d4', '#f97316'])
    
    plt.title(titulo)
    plt.tight_layout()
    
    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format='png', dpi=100)
    plt.close()
    img_buffer.seek(0)
    return img_buffer


def _generar_reporte_con_groq(prompt: str, datos: dict) -> str:
    """Envía datos reales a Groq para generar reporte ejecutivo detallado"""
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}

    contexto = f"""
DATOS REALES DE LA PLATAFORMA (Periodo: {datos['fecha_inicio']} al {datos['fecha_fin']}):
- Total incidentes: {datos['total_incidentes']}
- Tasa de éxito: {datos['tasa_exito']}%
- Ingresos totales: {datos['ingresos_totales_bs']} Bs.
- Calificación promedio: {datos['calificacion_promedio']}/5
- Distribución de estados: {json.dumps(datos['estados_dist'])}
- Distribución de prioridades: {json.dumps(datos['prio_dist'])}
"""
    sistema = (
        "Eres un analista de datos experto en operaciones logísticas. "
        "Tu objetivo es proporcionar reportes extremadamente detallados y profesionales. "
        "Estructura el reporte con: Título, Resumen Ejecutivo, Análisis Métrico, Tendencias y Recomendaciones Strategicas. "
        "Responde en español usando Markdown enriquecido."
    )

    body = {
        "model": "llama-3.3-70b-versatile",
        "messages": [
            {"role": "system", "content": sistema},
            {"role": "user", "content": f"Solicitud del usuario: \"{prompt}\"\n\n{contexto}"}
        ],
        "temperature": 0.4,
        "max_tokens": 3000
    }

    try:
        res = requests.post(url, headers=headers, json=body, timeout=40)
        if res.status_code == 200:
            return res.json()["choices"][0]["message"]["content"]
    except Exception as e:
        print(f"Excepción Groq: {e}")

    return "No se pudo generar el análisis detallado. Datos:\n\n" + contexto


def _transcribir_audio_reporte(audio_bytes: bytes) -> str:
    """Transcribe audio a texto usando Groq Whisper"""
    url = "https://api.groq.com/openai/v1/audio/transcriptions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}"}
    files = {"file": ("audio.m4a", audio_bytes, "audio/m4a")}
    data = {"model": "whisper-large-v3", "response_format": "json"}
    try:
        res = requests.post(url, headers=headers, files=files, data=data, timeout=15)
        if res.status_code == 200:
            return res.json().get("text", "").strip() or "Audio inaudible."
    except Exception as e:
        print(f"Error transcripción reporte: {e}")
    return "No se pudo transcribir el audio."


@router.post("/generar", response_model=ReporteResponse)
def generar_reporte_texto(
    datos: ReporteRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    metricas = _recopilar_datos_periodo(db, datos.periodo_dias, current_user)
    reporte = _generar_reporte_con_groq(datos.prompt, metricas)
    return ReporteResponse(
        reporte_markdown=reporte,
        prompt_procesado=datos.prompt,
        datos_periodo=metricas
    )


@router.post("/voz", response_model=ReporteResponse)
def generar_reporte_voz(
    datos: ReporteVozRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    try:
        audio_b64 = datos.audio_base64
        if "," in audio_b64: audio_b64 = audio_b64.split(",")[1]
        audio_bytes = base64.b64decode(audio_b64)
    except Exception: raise HTTPException(status_code=400, detail="Audio inválido.")

    prompt_transcrito = _transcribir_audio_reporte(audio_bytes)
    metricas = _recopilar_datos_periodo(db, datos.periodo_dias, current_user)
    reporte = _generar_reporte_con_groq(prompt_transcrito, metricas)

    return ReporteResponse(
        reporte_markdown=reporte,
        prompt_procesado=prompt_transcrito,
        datos_periodo=metricas
    )


@router.post("/exportar/excel")
def exportar_excel(
    datos: ReporteRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    metricas = _recopilar_datos_periodo(db, datos.periodo_dias, current_user)
    df_resumen = pd.DataFrame([{"Métrica": k, "Valor": v} for k, v in metricas.items() if not isinstance(v, (list, dict))])
    
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_resumen.to_excel(writer, sheet_name='Resumen Ejecutivo', index=False)
        if metricas.get("top_talleres"):
            pd.DataFrame(metricas["top_talleres"]).to_excel(writer, sheet_name='Top Talleres', index=False)
    
    output.seek(0)
    return StreamingResponse(
        output,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=reporte_kpis_{datetime.now().strftime('%Y%m%d')}.xlsx"}
    )


@router.post("/exportar/pdf")
def exportar_pdf(
    datos: ReporteRequest,
    db: Session = Depends(get_db),
    current_user: Usuario = Depends(get_current_user)
):
    """Genera un reporte PDF profesional con gráficas incluidas"""
    metricas = _recopilar_datos_periodo(db, datos.periodo_dias, current_user)
    
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    title_style = ParagraphStyle('TitleStyle', parent=styles['Heading1'], fontSize=22, alignment=1, spaceAfter=20, color=colors.HexColor("#1e293b"))
    subtitle_style = ParagraphStyle('SubtitleStyle', parent=styles['Heading2'], fontSize=16, spaceBefore=20, spaceAfter=10, color=colors.HexColor("#334155"))

    elements.append(Paragraph("Reporte de Analítica Operacional con Gráficos", title_style))
    elements.append(Paragraph(f"Periodo: {metricas['fecha_inicio']} al {metricas['fecha_fin']}", styles['Normal']))
    elements.append(Spacer(1, 0.3 * inch))

    # Métricas principales
    data = [
        ["Métrica Clave", "Valor"],
        ["Total Incidentes", str(metricas["total_incidentes"])],
        ["Tasa de Éxito", f"{metricas['tasa_exito']}%"],
        ["Ingresos Totales", f"{metricas['ingresos_totales_bs']} Bs"],
        ["Calificación Promedio", f"{metricas['calificacion_promedio']} ★"]
    ]
    t = Table(data, colWidths=[3*inch, 2*inch])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.HexColor("#1e293b")),
        ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('ALIGN', (0,0), (-1,-1), 'CENTER')
    ]))
    elements.append(t)
    elements.append(Spacer(1, 0.4 * inch))

    # Gráficas
    if metricas["incidentes_mes"]:
        elements.append(Paragraph("Evolución Mensual de Incidentes", subtitle_style))
        meses = [m["mes"] for m in metricas["incidentes_mes"]]
        totales = [m["total"] for m in metricas["incidentes_mes"]]
        img_mes = _generar_grafica_matplotlib(totales, meses, "Incidentes por Mes", 'bar')
        elements.append(Image(img_mes, width=5*inch, height=3*inch))
        elements.append(Spacer(1, 0.3 * inch))

    if metricas["estados_dist"]:
        elements.append(Paragraph("Distribución de Incidentes por Estado", subtitle_style))
        labels = list(metricas["estados_dist"].keys())
        values = list(metricas["estados_dist"].values())
        img_estado = _generar_grafica_matplotlib(values, labels, "Distribución Operativa", 'pie')
        elements.append(Image(img_estado, width=5*inch, height=3*inch))

    doc.build(elements)
    buffer.seek(0)
    
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": "attachment; filename=reporte_grafico.pdf"}
    )
