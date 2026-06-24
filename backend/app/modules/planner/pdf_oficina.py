# pdf_oficina.py — Reporte PDF Oficina/uso interno (ReportLab). Portado del fork.
# `output_path` acepta ruta o file-like (BytesIO). Las fotos llegan con ruta
# ABSOLUTA ya resuelta por app.storage.
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, PageBreak, Image
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from datetime import date, timedelta
import os, json

GREEN  = colors.HexColor("#62B989")
TEAL   = colors.HexColor("#20B2AA")
DARK   = colors.HexColor("#374560")
GRAY   = colors.HexColor("#EAEAEA")
MID    = colors.HexColor("#717070")
WHITE  = colors.white
BLACK  = colors.HexColor("#1A1A1A")
RED    = colors.HexColor("#E05555")
YELLOW = colors.HexColor("#F0B429")
W, H   = A4
COL    = W - 4*cm

def s(name, **kw):
    d = {"fontName":"Helvetica","textColor":BLACK,"fontSize":9,"leading":13}
    d.update(kw); return ParagraphStyle(name, **d)

S = {
    "h1":    s("h1",   fontSize=10, fontName="Helvetica-Bold", textColor=WHITE),
    "h2":    s("h2",   fontSize=10, fontName="Helvetica-Bold", textColor=DARK),
    "body":  s("body", fontSize=9),
    "small": s("small",fontSize=8,  textColor=MID, leading=11),
    "ctr":   s("ctr",  fontSize=9,  alignment=TA_CENTER),
    "right": s("right",fontSize=8,  alignment=TA_RIGHT, textColor=MID),
    "italic":s("italic",fontSize=8, fontName="Helvetica-Oblique", textColor=MID, leading=11),
    "badge": s("badge",fontSize=9,  fontName="Helvetica-Bold", textColor=WHITE, alignment=TA_CENTER),
}

def sec(text):
    t = Table([[Paragraph(f"  {text}", S['h1'])]], colWidths=[COL])
    t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),DARK),("LEFTPADDING",(0,0),(-1,-1),8),("TOPPADDING",(0,0),(-1,-1),6),("BOTTOMPADDING",(0,0),(-1,-1),6),("LINEBEFORE",(0,0),(0,-1),4,TEAL)]))
    return t

def badge(text, bg=TEAL):
    t = Table([[Paragraph(text, S['badge'])]], colWidths=[3*cm])
    t.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),bg),("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4),("LEFTPADDING",(0,0),(-1,-1),8),("RIGHTPADDING",(0,0),(-1,-1),8)]))
    return t

def generar_pdf_oficina(proyecto, actividades, cuadrillas, asistencia, snapshots, fotos,
    fecha_desde=None, fecha_hasta=None, tipo="semanal", semana_num=1,
    observaciones="", valorizaciones=None, output_path="reporte_oficina.pdf"):

    hoy = date.today()
    if not fecha_desde: fecha_desde = hoy - timedelta(days=hoy.weekday())
    if not fecha_hasta: fecha_hasta = fecha_desde + timedelta(days=6)
    valorizaciones = valorizaciones or []
    periodo = f"Semana {semana_num}" if tipo=="semanal" else f"{fecha_desde} — {fecha_hasta}"

    duracion = ""
    if proyecto.get("fecha_inicio") and proyecto.get("fecha_fin"):
        try: duracion = f"{(date.fromisoformat(str(proyecto['fecha_fin']))-date.fromisoformat(str(proyecto['fecha_inicio']))).days} días"
        except: pass

    presente = len([a for a in asistencia if a.get("estado")=="Presente"])
    tardanza = len([a for a in asistencia if a.get("estado")=="Tardanza"])
    ausente  = len([a for a in asistencia if a.get("estado")=="Ausente"])
    avr = proyecto.get("avance_real",0)
    avp = proyecto.get("avance_planificado",0)

    story = []
    story.append(Spacer(1, 0.5*cm))

    # ── HEADER ──
    hdr = Table([[
        Paragraph(f"<b>ENERGREEN PERÚ E.I.R.L.</b><br/><font size=9 color='#717070'>Reporte Técnico de Avance — {periodo}</font>", s("ht",fontSize=16,fontName="Helvetica-Bold",textColor=DARK,leading=20)),
        badge("USO INTERNO"),
    ]], colWidths=[COL*0.78, COL*0.22])
    hdr.setStyle(TableStyle([("VALIGN",(0,0),(-1,-1),"MIDDLE"),("LINEBELOW",(0,0),(-1,0),2,DARK),("TOPPADDING",(0,0),(-1,-1),8),("BOTTOMPADDING",(0,0),(-1,-1),8)]))
    story.append(hdr)
    story.append(Spacer(1,0.1*cm))
    story.append(Paragraph(f"<b>{proyecto.get('nombre','')}</b>  ·  Generado: {hoy.strftime('%d/%m/%Y %H:%M')}", S['small']))
    story.append(Spacer(1,0.3*cm))

    # ── KPIs técnicos ──
    kpi = Table([[
        Paragraph(f"<b>{avr:.1f}%</b>", s("k1",fontSize=20,fontName="Helvetica-Bold",textColor=WHITE,alignment=TA_CENTER)),
        Paragraph(f"<b>{avp:.1f}%</b>", s("k2",fontSize=20,fontName="Helvetica-Bold",textColor=TEAL,alignment=TA_CENTER)),
        Paragraph(f"<b>{proyecto.get('paneles',0)}</b>", s("k3",fontSize=20,fontName="Helvetica-Bold",textColor=DARK,alignment=TA_CENTER)),
        Paragraph(f"<b>{presente}</b>", s("k4",fontSize=20,fontName="Helvetica-Bold",textColor=GREEN,alignment=TA_CENTER)),
        Paragraph(f"<b>{tardanza}</b>", s("k5",fontSize=20,fontName="Helvetica-Bold",textColor=YELLOW,alignment=TA_CENTER)),
        Paragraph(f"<b>{ausente}</b>",  s("k6",fontSize=20,fontName="Helvetica-Bold",textColor=RED,alignment=TA_CENTER)),
    ],[
        Paragraph("Avance Real",  s("l1",fontSize=8,textColor=WHITE,alignment=TA_CENTER)),
        Paragraph("Planificado",  s("l2",fontSize=8,textColor=MID,alignment=TA_CENTER)),
        Paragraph("Paneles",      s("l3",fontSize=8,textColor=MID,alignment=TA_CENTER)),
        Paragraph("Presentes",    s("l4",fontSize=8,textColor=GREEN,alignment=TA_CENTER)),
        Paragraph("Tardanzas",    s("l5",fontSize=8,textColor=YELLOW,alignment=TA_CENTER)),
        Paragraph("Ausentes",     s("l6",fontSize=8,textColor=RED,alignment=TA_CENTER)),
    ]], colWidths=[COL/6]*6)
    kpi.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(0,-1),GREEN),
        ("BACKGROUND",(1,0),(5,-1),colors.HexColor("#F8F8F8")),
        ("BOX",(0,0),(-1,-1),1,GRAY),("INNERGRID",(0,0),(-1,-1),0.5,GRAY),
        ("TOPPADDING",(0,0),(-1,-1),8),("BOTTOMPADDING",(0,0),(-1,-1),6),
    ]))
    story.append(kpi)
    story.append(Spacer(1,0.4*cm))

    # ── DATOS GENERALES ──
    story.append(sec("DATOS DEL PROYECTO"))
    story.append(Spacer(1,0.2*cm))
    dg = Table([
        [Paragraph("<b>Proyecto:</b>",s("dgl",fontSize=9,textColor=MID,fontName="Helvetica-Bold")), Paragraph(proyecto.get("nombre",""),S['body']),
         Paragraph("<b>Estado:</b>",s("dgl2",fontSize=9,textColor=MID,fontName="Helvetica-Bold")), Paragraph(proyecto.get("estado",""),S['body'])],
        [Paragraph("<b>Cliente:</b>",s("dgl3",fontSize=9,textColor=MID,fontName="Helvetica-Bold")), Paragraph(proyecto.get("cliente") or "—",S['body']),
         Paragraph("<b>Región:</b>",s("dgl4",fontSize=9,textColor=MID,fontName="Helvetica-Bold")), Paragraph(proyecto.get("region") or "—",S['body'])],
        [Paragraph("<b>Ubicación:</b>",s("dgl5",fontSize=9,textColor=MID,fontName="Helvetica-Bold")), Paragraph(proyecto.get("ubicacion") or "—",S['body']),
         Paragraph("<b>Duración:</b>",s("dgl6",fontSize=9,textColor=MID,fontName="Helvetica-Bold")), Paragraph(duracion or "—",S['body'])],
        [Paragraph("<b>Período:</b>",s("dgl7",fontSize=9,textColor=MID,fontName="Helvetica-Bold")), Paragraph(f"{fecha_desde} al {fecha_hasta}",S['body']),
         Paragraph("<b>Paneles:</b>",s("dgl8",fontSize=9,textColor=MID,fontName="Helvetica-Bold")), Paragraph(str(proyecto.get("paneles",0)),S['body'])],
    ], colWidths=[COL*0.15,COL*0.35,COL*0.15,COL*0.35])
    dg.setStyle(TableStyle([("GRID",(0,0),(-1,-1),0.5,GRAY),("BACKGROUND",(0,0),(0,-1),colors.HexColor("#F8F8F8")),("BACKGROUND",(2,0),(2,-1),colors.HexColor("#F8F8F8")),("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5),("LEFTPADDING",(0,0),(-1,-1),8)]))
    story.append(dg)
    story.append(Spacer(1,0.3*cm))

    # ── CUADRILLAS ──
    story.append(sec("CUADRILLAS DEL PROYECTO"))
    story.append(Spacer(1,0.2*cm))
    if cuadrillas:
        for c in cuadrillas:
            miembros = [m for m in c.get("miembros",[]) if m.get("activo",True)]
            ch = Table([[Paragraph(f"<font color='white'><b>👷 {c.get('nombre','')}</b>  ({len(miembros)} miembros)</font>",S['h1'])]], colWidths=[COL])
            ch.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),DARK),("TOPPADDING",(0,0),(-1,-1),7),("BOTTOMPADDING",(0,0),(-1,-1),7),("LEFTPADDING",(0,0),(-1,-1),10)]))
            story.append(ch)
            if miembros:
                mh = [Paragraph(f"<b>{t}</b>",S['ctr']) for t in ["Nombre","Rol Interno","Profesión","F.Ingreso"]]
                mrows = [mh]
                for m in miembros:
                    mrows.append([
                        Paragraph(m.get("nombre_persona",""),S['body']),
                        Paragraph(m.get("rol_interno",""),s("mr",fontSize=9,textColor=TEAL,fontName="Helvetica-Bold")),
                        Paragraph(m.get("profesion",""),S['small']),
                        Paragraph(str(m.get("fecha_ingreso") or "—"),S['small']),
                    ])
                mt = Table(mrows, colWidths=[COL*0.32,COL*0.25,COL*0.28,COL*0.15])
                mt.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),colors.HexColor("#F0F0F0")),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),8),("GRID",(0,0),(-1,-1),0.5,GRAY),("ROWBACKGROUNDS",(0,1),(-1,-1),[WHITE,colors.HexColor("#F9F9F9")]),("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4),("LEFTPADDING",(0,0),(-1,-1),6)]))
                story.append(mt)
            story.append(Spacer(1,0.25*cm))
    else:
        story.append(Paragraph("Sin cuadrillas registradas.",S['small']))

    story.append(PageBreak())
    story.append(Spacer(1,0.3*cm))
    story.append(Paragraph(f"<b>{proyecto.get('nombre','')}</b>  ·  Actividades y Asistencia  ·  <font color='#717070'>{periodo}</font>",S['body']))
    story.append(Spacer(1,0.3*cm))

    # ── ACTIVIDADES DETALLADAS ──
    story.append(sec("PLAN DE ACTIVIDADES (DETALLE COMPLETO)"))
    story.append(Spacer(1,0.2*cm))
    acts_h = [Paragraph(f"<b>{t}</b>",S['ctr']) for t in ["#","Actividad","Estado","Prioridad","F.Inicio","F.Fin","Avance","Subtareas"]]
    acts_rows = [acts_h]
    for i,a in enumerate([x for x in actividades if x.get("nivel",1)>0]):
        subs = a.get("subtareas") or []
        if isinstance(subs, str):
            try: subs = json.loads(subs)
            except Exception: subs = []
        hechas=len([x for x in subs if x.get("hecho")])
        ec={"Completado":"#166534","En curso":"#1e40af","Pendiente":"#717070","Bloqueado":"#991b1b"}.get(a.get("estado",""),"#717070")
        pc={"Alta":"#E05555","Media":"#F0B429","Baja":"#62B989"}.get(a.get("prioridad",""),"#717070")
        av=a.get("avance",0)
        acts_rows.append([
            Paragraph(str(i+1),S['ctr']),
            Paragraph("  "*a.get("nivel",1)+a.get("titulo",""),S['body']),
            Paragraph(f"<font color='{ec}'>{a.get('estado','')}</font>",s("es",fontSize=8,alignment=TA_CENTER)),
            Paragraph(f"<font color='{pc}'><b>{a.get('prioridad','')}</b></font>",s("ps",fontSize=8,alignment=TA_CENTER)),
            Paragraph(str(a.get("fecha_inicio_plan") or "—"),S['ctr']),
            Paragraph(str(a.get("fecha_fin_plan") or "—"),S['ctr']),
            Paragraph(f"{av:.0f}%",S['ctr']),
            Paragraph(f"{hechas}/{len(subs)}" if subs else "—",S['ctr']),
        ])
    at = Table(acts_rows, colWidths=[COL*0.04,COL*0.28,COL*0.10,COL*0.10,COL*0.11,COL*0.11,COL*0.10,COL*0.10])
    at.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),DARK),("TEXTCOLOR",(0,0),(-1,0),WHITE),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),8),("GRID",(0,0),(-1,-1),0.5,GRAY),("ROWBACKGROUNDS",(0,1),(-1,-1),[WHITE,colors.HexColor("#F8FFFE")]),("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4),("LEFTPADDING",(0,0),(-1,-1),4)]))
    story.append(at)
    story.append(Spacer(1,0.4*cm))

    # ── ASISTENCIA ──
    story.append(sec("REGISTRO DE ASISTENCIA — " + str(periodo)))
    story.append(Spacer(1,0.2*cm))
    resumen = Table([[
        Paragraph(f"<b>{presente}</b><br/><font size=8>Presentes</font>", s("ap",fontSize=18,fontName="Helvetica-Bold",textColor=GREEN,alignment=TA_CENTER,leading=22)),
        Paragraph(f"<b>{tardanza}</b><br/><font size=8>Tardanzas</font>", s("at",fontSize=18,fontName="Helvetica-Bold",textColor=YELLOW,alignment=TA_CENTER,leading=22)),
        Paragraph(f"<b>{ausente}</b><br/><font size=8>Ausentes</font>",  s("aa",fontSize=18,fontName="Helvetica-Bold",textColor=RED,alignment=TA_CENTER,leading=22)),
    ]], colWidths=[COL/3]*3)
    resumen.setStyle(TableStyle([("BOX",(0,0),(-1,-1),1,GRAY),("INNERGRID",(0,0),(-1,-1),0.5,GRAY),("TOPPADDING",(0,0),(-1,-1),10),("BOTTOMPADDING",(0,0),(-1,-1),10)]))
    story.append(resumen)
    story.append(Spacer(1,0.3*cm))
    if asistencia:
        ah = [Paragraph(f"<b>{t}</b>",S['ctr']) for t in ["Nombre","Fecha","Estado","Hora","Observación"]]
        arows = [ah]
        for a in asistencia:
            ec={"Presente":"#166534","Tardanza":"#854d0e","Ausente":"#991b1b"}.get(a.get("estado",""),"#717070")
            arows.append([
                Paragraph(a.get("nombre_persona") or f"#{a.get('persona_id','')}",S['body']),
                Paragraph(str(a.get("fecha","")),S['ctr']),
                Paragraph(f"<font color='{ec}'><b>{a.get('estado','')}</b></font>",s("ae",fontSize=8,alignment=TA_CENTER)),
                Paragraph(a.get("hora") or "—",S['ctr']),
                Paragraph(a.get("observacion") or "—",S['small']),
            ])
        ast = Table(arows, colWidths=[COL*0.28,COL*0.15,COL*0.13,COL*0.10,COL*0.34])
        ast.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),DARK),("TEXTCOLOR",(0,0),(-1,0),WHITE),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),8),("GRID",(0,0),(-1,-1),0.5,GRAY),("ROWBACKGROUNDS",(0,1),(-1,-1),[WHITE,colors.HexColor("#F9F9F9")]),("TOPPADDING",(0,0),(-1,-1),4),("BOTTOMPADDING",(0,0),(-1,-1),4),("LEFTPADDING",(0,0),(-1,-1),6)]))
        story.append(ast)
    else:
        story.append(Paragraph("Sin registros de asistencia en el período.",S['small']))

    story.append(PageBreak())
    story.append(Spacer(1,0.3*cm))

    # ── CURVA S ──
    story.append(sec("CURVA S — AVANCE ACUMULADO"))
    story.append(Spacer(1,0.2*cm))
    diff = avr - avp
    cr = Table([[
        Paragraph(f"<b>{avp:.1f}%</b><br/><font size=8>Planificado</font>", s("cr1",fontSize=20,fontName="Helvetica-Bold",textColor=TEAL,alignment=TA_CENTER,leading=24)),
        Paragraph(f"<b>{avr:.1f}%</b><br/><font size=8 color='white'>Real</font>", s("cr2",fontSize=20,fontName="Helvetica-Bold",textColor=WHITE,alignment=TA_CENTER,leading=24)),
        Paragraph(f"<b>{'+' if diff>=0 else ''}{diff:.1f}%</b><br/><font size=8 color='white'>Delta</font>", s("cr3",fontSize=20,fontName="Helvetica-Bold",textColor=WHITE,alignment=TA_CENTER,leading=24)),
    ]], colWidths=[COL/3]*3)
    cr.setStyle(TableStyle([("BACKGROUND",(0,0),(0,0),colors.HexColor("#F0F9FF")),("BACKGROUND",(1,0),(1,0),GREEN),("BACKGROUND",(2,0),(2,0),GREEN if diff>=0 else RED),("BOX",(0,0),(-1,-1),1,GRAY),("INNERGRID",(0,0),(-1,-1),0.5,GRAY),("TOPPADDING",(0,0),(-1,-1),12),("BOTTOMPADDING",(0,0),(-1,-1),12)]))
    story.append(cr)
    story.append(Spacer(1,0.3*cm))
    if snapshots:
        sh2=[Paragraph(f"<b>{t}</b>",S['ctr']) for t in ["Sem","Fecha","% Previsto","% Real","Delta","Actividades"]]
        srows=[sh2]
        for i,snap in enumerate(snapshots[:12]):
            d=snap["avance_real"]-snap["avance_planificado"]
            srows.append([
                Paragraph(f"S{i+1}",S['ctr']),
                Paragraph(str(snap["fecha"]),S['ctr']),
                Paragraph(f"{snap['avance_planificado']:.1f}%",s("sv1",fontSize=9,alignment=TA_CENTER,textColor=TEAL)),
                Paragraph(f"{snap['avance_real']:.1f}%",s("sv2",fontSize=9,fontName="Helvetica-Bold",alignment=TA_CENTER,textColor=GREEN)),
                Paragraph(f"{'+' if d>=0 else ''}{d:.1f}%",s("sv3",fontSize=9,fontName="Helvetica-Bold",alignment=TA_CENTER,textColor=GREEN if d>=0 else RED)),
                Paragraph(f"{snap.get('actividades_hechas',0)}/{snap.get('actividades_total',0)}",S['ctr']),
            ])
        st2=Table(srows, colWidths=[COL*0.08,COL*0.20,COL*0.18,COL*0.18,COL*0.18,COL*0.18])
        st2.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),DARK),("TEXTCOLOR",(0,0),(-1,0),WHITE),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),9),("GRID",(0,0),(-1,-1),0.5,GRAY),("ROWBACKGROUNDS",(0,1),(-1,-1),[WHITE,colors.HexColor("#F8FFFE")]),("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5)]))
        story.append(st2)
    else:
        story.append(Paragraph("Sin snapshots registrados.",S['small']))
    story.append(Spacer(1,0.4*cm))

    # ── VALORIZACIONES ──
    story.append(sec("ESTADO DE VALORIZACIONES"))
    story.append(Spacer(1,0.2*cm))
    vh=[Paragraph(f"<b>{t}</b>",S['ctr']) for t in ["#","Período","% Avance","Monto","N° Factura","Estado"]]
    vrows=[vh]
    if valorizaciones:
        for v in valorizaciones:
            vrows.append([Paragraph(str(v.get("numero","")),S['ctr']),Paragraph(v.get("periodo",""),S['body']),Paragraph(v.get("porcentaje",""),S['ctr']),Paragraph(v.get("monto",""),S['ctr']),Paragraph(v.get("factura",""),S['body']),Paragraph(v.get("estado",""),S['ctr'])])
    else:
        vrows.append([Paragraph("Sin valorizaciones registradas.",s("vr",fontSize=9,textColor=MID))]+[""]*(5))
    vt=Table(vrows, colWidths=[COL*0.05,COL*0.22,COL*0.13,COL*0.18,COL*0.20,COL*0.22])
    vt.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,0),DARK),("TEXTCOLOR",(0,0),(-1,0),WHITE),("FONTNAME",(0,0),(-1,0),"Helvetica-Bold"),("FONTSIZE",(0,0),(-1,-1),8),("GRID",(0,0),(-1,-1),0.5,GRAY),("ROWBACKGROUNDS",(0,1),(-1,-1),[WHITE,colors.HexColor("#F9F9F9")]),("TOPPADDING",(0,0),(-1,-1),5),("BOTTOMPADDING",(0,0),(-1,-1),5)]))
    story.append(vt)
    story.append(Spacer(1,0.4*cm))

    # ── OBSERVACIONES ──
    story.append(sec("OBSERVACIONES / COMENTARIOS INTERNOS"))
    story.append(Spacer(1,0.2*cm))
    ot=Table([[Paragraph(observaciones or "Sin observaciones para este período.",S['body'])]], colWidths=[COL])
    ot.setStyle(TableStyle([("BACKGROUND",(0,0),(-1,-1),colors.HexColor("#FFFBF0")),("BOX",(0,0),(-1,-1),1,GRAY),("TOPPADDING",(0,0),(-1,-1),10),("BOTTOMPADDING",(0,0),(-1,-1),10),("LEFTPADDING",(0,0),(-1,-1),12),("MINROWHEIGHT",(0,0),(-1,-1),50)]))
    story.append(ot)
    story.append(Spacer(1,0.3*cm))
    story.append(HRFlowable(width=COL,thickness=2,color=GRAY))
    story.append(Spacer(1,0.2*cm))
    story.append(Table([[Paragraph("ENERGREEN PERÚ E.I.R.L. — DOCUMENTO USO INTERNO — Planner Solar",S['small']),Paragraph(hoy.strftime("%d/%m/%Y"),S['right'])]], colWidths=[COL*0.75,COL*0.25]))

    # ── FOTOS (rutas absolutas ya resueltas por storage) ──
    if fotos:
        story.append(PageBreak())
        story.append(Spacer(1,0.3*cm))
        story.append(sec(f"REGISTRO FOTOGRÁFICO COMPLETO ({len(fotos)} fotos)"))
        story.append(Spacer(1,0.3*cm))
        fw=(COL-0.8*cm)/4
        row=[]
        for f in fotos:
            try:
                ruta=f.get("ruta","")
                if ruta and os.path.exists(ruta):
                    img=Image(ruta,width=fw,height=fw*0.75)
                    com=f.get("comentario_pdf","") or f"Etapa {f.get('etapa','')}"
                    pdf_mark = "✓ En reporte cliente" if f.get("incluir_en_pdf") else ""
                    cell=Table([[img],[Paragraph(f"<b>{f.get('emoji','📷')} {f.get('etapa','')}</b>",S['small'])],[Paragraph(f"📅 {f.get('fecha','')}",S['small'])],[Paragraph(f"<i>{com[:60]}</i>",S['italic'])],[Paragraph(pdf_mark,s("pm",fontSize=7,textColor=GREEN))]], colWidths=[fw])
                    cell.setStyle(TableStyle([("BOX",(0,0),(-1,-1),0.5,GRAY),("TOPPADDING",(0,0),(-1,-1),3),("BOTTOMPADDING",(0,0),(-1,-1),3),("LEFTPADDING",(0,0),(-1,-1),3),("RIGHTPADDING",(0,0),(-1,-1),3)]))
                    row.append(cell)
                else: row.append(Paragraph("",S['small']))
            except: row.append(Paragraph("",S['small']))
            if len(row)==4:
                story.append(Table([row],colWidths=[fw]*4))
                story.append(Spacer(1,0.2*cm)); row=[]
        if row:
            while len(row)<4: row.append(Paragraph("",S['small']))
            story.append(Table([row],colWidths=[fw]*4))

    doc=SimpleDocTemplate(output_path, pagesize=A4, leftMargin=2*cm, rightMargin=2*cm, topMargin=2*cm, bottomMargin=2*cm,
        title=f"Reporte Oficina — {proyecto.get('nombre','')}", author="ENERGREEN PERÚ")
    doc.build(story)
    return output_path
