# pdf_cliente.py — Reporte PDF Cliente (ReportLab). Portado del módulo PLANNER.
# `output_path` acepta una ruta o un file-like (BytesIO) → el router pasa un buffer
# en memoria para no dejar archivos temporales. Las fotos llegan con ruta ABSOLUTA
# ya resuelta por app.storage.
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, PageBreak, Image
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from datetime import date, timedelta
import os

GREEN  = colors.HexColor("#62B989")
TEAL   = colors.HexColor("#20B2AA")
DARK   = colors.HexColor("#374560")
GRAY   = colors.HexColor("#EAEAEA")
MID    = colors.HexColor("#717070")
WHITE  = colors.white
BLACK  = colors.HexColor("#1A1A1A")
RED    = colors.HexColor("#E05555")
W, H   = A4

def st(name, **kw):
    defaults = {"fontName":"Helvetica","textColor":BLACK,"fontSize":9,"leading":13}
    defaults.update(kw)
    return ParagraphStyle(name, **defaults)

STYLES = {
    "title":  st("title",  fontSize=20, fontName="Helvetica-Bold", textColor=DARK, leading=24),
    "h1":     st("h1",     fontSize=10, fontName="Helvetica-Bold", textColor=WHITE, leading=13),
    "h2":     st("h2",     fontSize=10, fontName="Helvetica-Bold", textColor=DARK,  leading=13),
    "body":   st("body",   fontSize=9,  leading=13),
    "small":  st("small",  fontSize=8,  textColor=MID, leading=11),
    "center": st("center", fontSize=9,  alignment=TA_CENTER, leading=12),
    "right":  st("right",  fontSize=8,  alignment=TA_RIGHT,  textColor=MID, leading=11),
    "italic": st("italic", fontSize=8,  fontName="Helvetica-Oblique", textColor=MID, leading=11),
    "green":  st("green",  fontSize=22, fontName="Helvetica-Bold", textColor=GREEN, alignment=TA_CENTER, leading=26),
    "teal":   st("teal",   fontSize=22, fontName="Helvetica-Bold", textColor=TEAL,  alignment=TA_CENTER, leading=26),
    "lbl":    st("lbl",    fontSize=8,  textColor=MID, alignment=TA_CENTER, leading=10),
}

COL = W - 4*cm

def section(text):
    t = Table([[Paragraph(f"  {text}", STYLES['h1'])]], colWidths=[COL])
    t.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),DARK),
        ("LEFTPADDING",(0,0),(-1,-1),8),("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6),
        ("LINEAFTER",(0,0),(0,-1),4,GREEN),
    ]))
    return t

def generar_pdf_cliente(proyecto, actividades, snapshots, fotos,
    fecha_desde=None, fecha_hasta=None, tipo="semanal",
    semana_num=1, observaciones="", output_path="reporte_cliente.pdf"):

    hoy = date.today()
    if not fecha_desde: fecha_desde = hoy - timedelta(days=hoy.weekday())
    if not fecha_hasta: fecha_hasta = fecha_desde + timedelta(days=6)
    periodo = f"Semana {semana_num}" if tipo=="semanal" else f"{fecha_desde} — {fecha_hasta}"

    duracion = ""
    if proyecto.get("fecha_inicio") and proyecto.get("fecha_fin"):
        try:
            duracion = f"{(date.fromisoformat(str(proyecto['fecha_fin'])) - date.fromisoformat(str(proyecto['fecha_inicio']))).days} días"
        except: pass

    story = []
    story.append(Spacer(1, 0.8*cm))

    # ── HEADER ──
    hdr = Table([[
        Paragraph("<b>ENERGREEN PERÚ</b><br/><font size=9 color='#717070'>E.I.R.L. — Gestión de Proyectos Fotovoltaicos</font>", STYLES['title']),
        Paragraph(f"<font color='white'><b>Reporte de Avance</b><br/>{periodo}<br/><font size=8>{hoy.strftime('%d/%m/%Y')}</font></font>", STYLES['center']),
    ]], colWidths=[COL*0.62, COL*0.38])
    hdr.setStyle(TableStyle([
        ("BACKGROUND",(1,0),(1,0),GREEN),("ALIGN",(1,0),(1,0),"CENTER"),
        ("VALIGN",(0,0),(-1,-1),"MIDDLE"),
        ("TOPPADDING",(0,0),(-1,-1),10),("BOTTOMPADDING",(0,0),(-1,-1),10),
        ("LEFTPADDING",(0,0),(-1,-1),8),("RIGHTPADDING",(0,0),(-1,-1),8),
        ("LINEBELOW",(0,0),(-1,0),3,GREEN),
    ]))
    story.append(hdr)
    story.append(Spacer(1, 0.4*cm))

    # ── BANNER PROYECTO ──
    banner = Table([[Paragraph(
        f"<font color='white'><font size=8>PROYECTO</font>   <b>{proyecto.get('nombre','')}</b></font>",
        STYLES['h1']
    )]], colWidths=[COL])
    banner.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),DARK),
        ("TOPPADDING",(0,0),(-1,-1),12),("BOTTOMPADDING",(0,0),(-1,-1),12),
        ("LEFTPADDING",(0,0),(-1,-1),16),
    ]))
    story.append(banner)

    info = Table([[
        Paragraph(f"🏢 {proyecto.get('cliente') or '—'}", STYLES['small']),
        Paragraph(f"📍 {proyecto.get('ubicacion') or '—'}", STYLES['small']),
        Paragraph(f"☀️ {proyecto.get('paneles',0)} paneles", STYLES['small']),
        Paragraph(f"⏱ {duracion or '—'}", STYLES['small']),
    ]], colWidths=[COL/4]*4)
    info.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#F0FFF8")),
        ("TOPPADDING",(0,0),(-1,-1),7),("BOTTOMPADDING",(0,0),(-1,-1),7),
        ("ALIGN",(0,0),(-1,-1),"CENTER"),("LINEBELOW",(0,0),(-1,0),1,GREEN),
    ]))
    story.append(info)
    story.append(Spacer(1, 0.4*cm))

    # ── KPIs ──
    avr = proyecto.get("avance_real",0)
    avp = proyecto.get("avance_planificado",0)
    kpi = Table([[
        Paragraph(f"<b>{avr:.0f}%</b>", STYLES['green']),
        Paragraph(f"<b>{avp:.0f}%</b>", STYLES['teal']),
        Paragraph(f"<b>{proyecto.get('paneles',0)}</b>", ParagraphStyle("kd",fontSize=22,fontName="Helvetica-Bold",textColor=DARK,alignment=TA_CENTER)),
        Paragraph(f"<b>{proyecto.get('estado','—')}</b>", ParagraphStyle("km",fontSize=14,fontName="Helvetica-Bold",textColor=MID,alignment=TA_CENTER)),
    ],[
        Paragraph("Avance Real", STYLES['lbl']),
        Paragraph("Planificado", STYLES['lbl']),
        Paragraph("Paneles", STYLES['lbl']),
        Paragraph("Estado", STYLES['lbl']),
    ]], colWidths=[COL/4]*4)
    kpi.setStyle(TableStyle([
        ("BOX",(0,0),(-1,-1),1,GRAY),("INNERGRID",(0,0),(-1,-1),0.5,GRAY),
        ("TOPPADDING",(0,0),(-1,-1),8),("BOTTOMPADDING",(0,0),(-1,-1),8),
    ]))
    story.append(kpi)
    story.append(Spacer(1, 0.5*cm))

    # ── 1. DATOS GENERALES ──
    story.append(section("1. DATOS GENERALES"))
    story.append(Spacer(1,0.2*cm))
    dg = Table([
        [Paragraph("<b>Proyecto:</b>",st("x",fontSize=9,textColor=MID,fontName="Helvetica-Bold")), Paragraph(proyecto.get("nombre",""),STYLES['body']),
         Paragraph("<b>Contratista:</b>",st("x2",fontSize=9,textColor=MID,fontName="Helvetica-Bold")), Paragraph("ENERGREEN PERÚ E.I.R.L.",STYLES['body'])],
        [Paragraph("<b>Cliente:</b>",st("x3",fontSize=9,textColor=MID,fontName="Helvetica-Bold")), Paragraph(proyecto.get("cliente") or "—",STYLES['body']),
         Paragraph("<b>Inicio:</b>",st("x4",fontSize=9,textColor=MID,fontName="Helvetica-Bold")), Paragraph(str(proyecto.get("fecha_inicio") or "—"),STYLES['body'])],
        [Paragraph("<b>Ubicación:</b>",st("x5",fontSize=9,textColor=MID,fontName="Helvetica-Bold")), Paragraph(proyecto.get("ubicacion") or "—",STYLES['body']),
         Paragraph("<b>Fin:</b>",st("x6",fontSize=9,textColor=MID,fontName="Helvetica-Bold")), Paragraph(str(proyecto.get("fecha_fin") or "—"),STYLES['body'])],
        [Paragraph("<b>Período:</b>",st("x7",fontSize=9,textColor=MID,fontName="Helvetica-Bold")), Paragraph(f"{fecha_desde} al {fecha_hasta}",STYLES['body']),
         Paragraph("<b>Duración:</b>",st("x8",fontSize=9,textColor=MID,fontName="Helvetica-Bold")), Paragraph(duracion or "—",STYLES['body'])],
    ], colWidths=[COL*0.18, COL*0.32, COL*0.18, COL*0.32])
    dg.setStyle(TableStyle([
        ("GRID",(0,0),(-1,-1),0.5,GRAY),
        ("BACKGROUND",(0,0),(0,-1),colors.HexColor("#F8F8F8")),
        ("BACKGROUND",(2,0),(2,-1),colors.HexColor("#F8F8F8")),
        ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
        ("LEFTPADDING",(0,0),(-1,-1),8),
    ]))
    story.append(dg)
    story.append(Spacer(1,0.4*cm))

    # ── 2. ALCANCE ──
    story.append(section("2. ALCANCE DEL PROYECTO"))
    story.append(Spacer(1,0.2*cm))
    atbl = Table([[Paragraph(proyecto.get("alcance") or "Sin descripción de alcance.",STYLES['body'])]], colWidths=[COL])
    atbl.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#F8FFFE")),("BOX",(0,0),(-1,-1),1,GRAY),("TOPPADDING",(0,0),(-1,-1),10),("BOTTOMPADDING",(0,0),(-1,-1),10),("LEFTPADDING",(0,0),(-1,-1),12)]))
    story.append(atbl)
    story.append(Spacer(1,0.4*cm))

    # ── 3. ACTIVIDADES ──
    story.append(section("3. ACTIVIDADES RELEVANTES DEL PERÍODO"))
    story.append(Spacer(1,0.2*cm))
    acts = [a for a in actividades if a.get("nivel",1)>0 and (a.get("avance",0)>0 or a.get("estado") in ["En curso","Completado"])][:8]
    if acts:
        for a in acts:
            ec = "#166534" if a.get("estado")=="Completado" else "#1e40af" if a.get("estado")=="En curso" else "#717070"
            r = Table([[
                Paragraph(f"● <b>{a.get('titulo','')}</b>", STYLES['body']),
                Paragraph(f"<font color='{ec}'>{a.get('estado','')}</font> · {a.get('avance',0):.0f}%", STYLES['small']),
            ]], colWidths=[COL*0.7, COL*0.3])
            r.setStyle(TableStyle([("LINEBELOW",(0,0),(-1,0),0.5,GRAY),("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),("LEFTPADDING",(0,0),(0,0),8)]))
            story.append(r)
    else:
        story.append(Paragraph("Sin actividades con avance en el período.", STYLES['small']))

    story.append(PageBreak())
    story.append(Spacer(1,0.3*cm))

    # ── 4. GANTT ──
    story.append(section("4. CRONOGRAMA POR FASES (GANTT)"))
    story.append(Spacer(1,0.2*cm))
    acts_g = [a for a in actividades if a.get("nivel",1)>0][:12]
    if acts_g:
        hrow = [Paragraph(f"<b>{t}</b>",STYLES['center']) for t in ["#","Actividad","F.Inicio","F.Fin","Días","% Real","% Prev","Delta"]]
        rows = [hrow]
        for i,a in enumerate(acts_g):
            av = a.get("avance",0)
            d = 0.0
            ds = ParagraphStyle("ds",fontSize=8,alignment=TA_CENTER,textColor=GREEN if d>=0 else RED)
            rows.append([
                Paragraph(str(i+1),STYLES['center']),
                Paragraph("  "*a.get("nivel",1)+a.get("titulo",""),STYLES['body']),
                Paragraph(str(a.get("fecha_inicio_plan") or "—"),STYLES['center']),
                Paragraph(str(a.get("fecha_fin_plan") or "—"),STYLES['center']),
                Paragraph(str(a.get("duracion_dias",0))+"d",STYLES['center']),
                Paragraph(f"{av:.0f}%",STYLES['center']),
                Paragraph(f"{av:.0f}%",STYLES['center']),
                Paragraph(f"+0.0%",ds),
            ])
        gt = Table(rows, colWidths=[COL*0.05,COL*0.31,COL*0.12,COL*0.12,COL*0.07,COL*0.11,COL*0.11,COL*0.11])
        gt.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0),DARK),("TEXTCOLOR",(0,0),(-1,0),WHITE),
            ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),8),
            ("GRID",(0,0),(-1,-1),0.5,GRAY),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[WHITE,colors.HexColor("#F8FFFE")]),
            ("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),
            ("LEFTPADDING",(0,0),(-1,-1),4),
        ]))
        story.append(gt)
    else:
        story.append(Paragraph("Sin actividades registradas.",STYLES['small']))
    story.append(Spacer(1,0.5*cm))

    # ── 5. CURVA S ──
    story.append(section("5. CURVA S DE AVANCE"))
    story.append(Spacer(1,0.2*cm))
    cr = Table([[
        Paragraph(f"<b>{avp:.1f}%</b><br/><font size=8 color='#717070'>Avance Planificado</font>", ParagraphStyle("cp",fontSize=22,fontName="Helvetica-Bold",textColor=TEAL,alignment=TA_CENTER,leading=28)),
        Paragraph(f"<b>{avr:.1f}%</b><br/><font size=8 color='rgba(255,255,255,0.8)'>Avance Real</font>", ParagraphStyle("cr2",fontSize=22,fontName="Helvetica-Bold",textColor=WHITE,alignment=TA_CENTER,leading=28)),
    ]], colWidths=[COL*0.5, COL*0.5])
    cr.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(0,0),colors.HexColor("#F0F9FF")),
        ("BACKGROUND",(1,0),(1,0),GREEN),
        ("BOX",(0,0),(-1,-1),1,GRAY),
        ("TOPPADDING",(0,0),(-1,-1),14),("BOTTOMPADDING",(0,0),(-1,-1),14),
    ]))
    story.append(cr)
    story.append(Spacer(1,0.3*cm))
    if snapshots:
        sh = [Paragraph(f"<b>{t}</b>",STYLES['center']) for t in ["Sem","Fecha","% Previsto","% Real","Delta"]]
        srows = [sh]
        for i,s in enumerate(snapshots[:12]):
            d = s["avance_real"]-s["avance_planificado"]
            srows.append([
                Paragraph(f"S{i+1}",STYLES['center']),
                Paragraph(str(s["fecha"]),STYLES['center']),
                Paragraph(f"{s['avance_planificado']:.1f}%",ParagraphStyle("sp2",fontSize=9,alignment=TA_CENTER,textColor=TEAL)),
                Paragraph(f"{s['avance_real']:.1f}%",ParagraphStyle("sr2",fontSize=9,fontName="Helvetica-Bold",alignment=TA_CENTER,textColor=GREEN)),
                Paragraph(f"{'+' if d>=0 else ''}{d:.1f}%",ParagraphStyle("sd2",fontSize=9,fontName="Helvetica-Bold",alignment=TA_CENTER,textColor=GREEN if d>=0 else RED)),
            ])
        st2 = Table(srows, colWidths=[COL*0.1,COL*0.25,COL*0.22,COL*0.22,COL*0.21])
        st2.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0),DARK),("TEXTCOLOR",(0,0),(-1,0),WHITE),
            ("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),9),
            ("GRID",(0,0),(-1,-1),0.5,GRAY),
            ("ROWBACKGROUNDS",(0,1),(-1,-1),[WHITE,colors.HexColor("#F8FFFE")]),
            ("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6),
        ]))
        story.append(st2)
    else:
        story.append(Paragraph("Sin snapshots registrados aún.",STYLES['small']))
    story.append(Spacer(1,0.4*cm))

    # ── 6. OBSERVACIONES ──
    story.append(section("6. OBSERVACIONES / COMENTARIOS"))
    story.append(Spacer(1,0.2*cm))
    ot = Table([[Paragraph(observaciones or "Sin observaciones para este período.",STYLES['body'])]], colWidths=[COL])
    ot.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#FFFBF0")),("BOX",(0,0),(-1,-1),1,GRAY),("TOPPADDING",(0,0),(-1,-1),10),("BOTTOMPADDING",(0,0),(-1,-1),10),("LEFTPADDING",(0,0),(-1,-1),12),("MINROWHEIGHT",(0,0),(-1,-1),50)]))
    story.append(ot)
    story.append(Spacer(1,0.4*cm))
    story.append(HRFlowable(width=COL,thickness=2,color=GRAY))
    story.append(Spacer(1,0.2*cm))
    story.append(Table([[
        Paragraph("ENERGREEN PERÚ E.I.R.L. — Planner Solar",STYLES['small']),
        Paragraph(hoy.strftime("%d/%m/%Y"),STYLES['right']),
    ]], colWidths=[COL*0.75, COL*0.25]))

    # ── 7. FOTOS (rutas absolutas ya resueltas por storage) ──
    fotos_pdf = [f for f in fotos if f.get("incluir_en_pdf",True) and f.get("ruta") and os.path.exists(f.get("ruta",""))]
    if fotos_pdf:
        story.append(PageBreak())
        story.append(Spacer(1,0.3*cm))
        story.append(section("7. REGISTRO FOTOGRÁFICO"))
        story.append(Spacer(1,0.3*cm))
        fw = (COL - 0.6*cm)/3
        row = []
        for i,f in enumerate(fotos_pdf[:12]):
            try:
                img = Image(f["ruta"], width=fw, height=fw*0.7)
                com = f.get("comentario_pdf","") or f"Etapa {f.get('etapa','General')}"
                cell = Table([[img],[Paragraph(f"<b>{f.get('emoji','📷')} {f.get('etapa','')}</b>",STYLES['small'])],[Paragraph(f"📅 {f.get('fecha','')}",STYLES['small'])],[Paragraph(f"<i>{com[:80]}</i>",STYLES['italic'])]], colWidths=[fw])
                cell.setStyle(TableStyle([("BOX",(0,0),(-1,-1),0.5,GRAY),("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4),("LEFTPADDING",(0,0),(-1,-1),4),("RIGHTPADDING",(0,0),(-1,-1),4)]))
                row.append(cell)
            except: row.append(Paragraph("",STYLES['small']))
            if len(row)==3:
                ft = Table([row], colWidths=[fw]*3)
                story.append(ft); story.append(Spacer(1,0.25*cm)); row=[]
        if row:
            while len(row)<3: row.append(Paragraph("",STYLES['small']))
            story.append(Table([row], colWidths=[fw]*3))

    doc = SimpleDocTemplate(output_path, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm,
        title=f"Reporte Cliente — {proyecto.get('nombre','')}", author="ENERGREEN PERÚ")
    doc.build(story)
    return output_path
