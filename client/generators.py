"""
client/generators.py
────────────────────
Generates DOCX documents (via docxtpl) and converts them to PDF
(via LibreOffice headless, with a reportlab fallback).

Usage example:
    from client.generators import generate_notice_pdf, generate_notice_docx

    ctx = {
        'ministry_name': 'Ministry of Home Affairs',
        'address': 'Singhadurbar,\nKathmandu, Nepal',
        'title': 'Temporary Closure on Public Holiday',
        'date': '05/07/2026',
        'body': 'This is to inform all citizens…',
    }
    pdf_bytes = generate_notice_pdf(ctx)   # bytes → HttpResponse
    docx_bytes = generate_notice_docx(ctx) # bytes → download DOCX
"""

import io
import os
import subprocess
import tempfile

from django.conf import settings


# ─────────────────────────────────────────────────────────────────────────────
# Internal helpers
# ─────────────────────────────────────────────────────────────────────────────

def _template_dir() -> str:
    path = os.path.join(settings.MEDIA_ROOT, "docx_templates")
    os.makedirs(path, exist_ok=True)
    return path


def _notice_template_path() -> str:
    return os.path.join(_template_dir(), "notice_template.docx")


def _job_template_path() -> str:
    return os.path.join(_template_dir(), "job_template.docx")


# ─── DOCX template builders (python-docx, run once) ─────────────────────────

def _build_notice_template(path: str) -> None:
    """Create the notice .docx template with Jinja2 placeholders."""
    from docx import Document
    from docx.shared import Pt, Cm, RGBColor
    from docx.enum.text import WD_ALIGN_PARAGRAPH

    doc = Document()

    # Page margins
    for sec in doc.sections:
        sec.top_margin    = Cm(2)
        sec.bottom_margin = Cm(2)
        sec.left_margin   = Cm(3)
        sec.right_margin  = Cm(2.5)

    # ── Header ────────────────────────────────────────────────
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("Government of Nepal")
    r.font.size = Pt(11)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("{{ministry_name}}")
    r.font.size = Pt(15)
    r.font.bold = True

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    r = p.add_run("{{address}}")
    r.font.size = Pt(9)

    doc.add_paragraph("")

    # Horizontal rule via border paragraph style
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
    p = doc.add_paragraph()
    p_pr = p._p.get_or_add_pPr()
    p_bdr = OxmlElement("w:pBdr")
    bottom = OxmlElement("w:bottom")
    bottom.set(qn("w:val"), "single")
    bottom.set(qn("w:sz"), "6")
    bottom.set(qn("w:space"), "4")
    bottom.set(qn("w:color"), "888888")
    p_bdr.append(bottom)
    p_pr.append(p_bdr)

    doc.add_paragraph("")

    # ── Document title ────────────────────────────────────────
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("{{title}}")
    r.font.size = Pt(11)
    r.font.bold = True
    r.font.underline = True

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run("Date: {{date}}")

    doc.add_paragraph("")

    # ── Body ─────────────────────────────────────────────────
    doc.add_paragraph("{{body}}")

    doc.save(path)


def _build_job_template(path: str) -> None:
    """Create the job listing .docx template with Jinja2 placeholders."""
    from docx import Document
    from docx.shared import Pt, Cm
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement

    doc = Document()
    for sec in doc.sections:
        sec.top_margin    = Cm(2)
        sec.bottom_margin = Cm(2)
        sec.left_margin   = Cm(3)
        sec.right_margin  = Cm(2.5)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run("Government of Nepal").font.size = Pt(11)

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("{{department}}")
    r.font.size = Pt(15)
    r.font.bold = True

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    p.add_run("{{location}}").font.size = Pt(9)

    doc.add_paragraph("")

    # HR
    p = doc.add_paragraph()
    ppr = p._p.get_or_add_pPr()
    pbdr = OxmlElement("w:pBdr")
    bot = OxmlElement("w:bottom")
    bot.set(qn("w:val"), "single")
    bot.set(qn("w:sz"), "6")
    bot.set(qn("w:space"), "4")
    bot.set(qn("w:color"), "888888")
    pbdr.append(bot)
    ppr.append(pbdr)

    doc.add_paragraph("")

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    r = p.add_run("{{title}}")
    r.font.bold = True
    r.font.underline = True

    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.add_run("Date: {{date}}")

    doc.add_paragraph("")

    for label, var in [
        ("",                       "{{description}}"),
        ("Requirements: ",         "{{requirements}}"),
        ("Age Requirement: ",      "{{age_requirement}}"),
        ("Deadline: ",             "{{deadline}}"),
        ("Contact Information: ",  "{{contact}}"),
    ]:
        p = doc.add_paragraph()
        if label:
            run = p.add_run(label)
            run.font.bold = True
        p.add_run(var)

    doc.save(path)


# ─── DOCX rendering via docxtpl ──────────────────────────────────────────────

def _render_docx(template_path: str, context: dict) -> bytes:
    """Render a docxtpl template and return DOCX bytes."""
    from docxtpl import DocxTemplate
    tpl = DocxTemplate(template_path)
    tpl.render(context)
    buf = io.BytesIO()
    tpl.save(buf)
    return buf.getvalue()


# ─── PDF conversion: LibreOffice → reportlab fallback ────────────────────────

def _libreoffice_pdf(docx_bytes: bytes) -> bytes | None:
    """Convert DOCX bytes to PDF using LibreOffice headless."""
    lo = None
    for candidate in ("libreoffice", "soffice"):
        try:
            res = subprocess.run(["which", candidate], capture_output=True, timeout=5)
            if res.returncode == 0:
                lo = candidate
                break
        except Exception:
            pass

    if not lo:
        return None

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            docx_path = os.path.join(tmpdir, "doc.docx")
            with open(docx_path, "wb") as f:
                f.write(docx_bytes)

            res = subprocess.run(
                [lo, "--headless", "--convert-to", "pdf", "--outdir", tmpdir, docx_path],
                capture_output=True, timeout=60,
            )
            pdf_path = os.path.join(tmpdir, "doc.pdf")
            if res.returncode == 0 and os.path.exists(pdf_path):
                with open(pdf_path, "rb") as f:
                    return f.read()
    except Exception:
        pass

    return None


# ─── Reportlab fallbacks ─────────────────────────────────────────────────────

def _notice_pdf_fallback(ctx: dict) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            topMargin=2*cm, bottomMargin=2*cm,
                            leftMargin=3*cm, rightMargin=2.5*cm)
    S = getSampleStyleSheet()
    center  = ParagraphStyle("c", parent=S["Normal"], alignment=TA_CENTER)
    right   = ParagraphStyle("r", parent=S["Normal"], alignment=TA_RIGHT, fontSize=9)
    bold_c  = ParagraphStyle("bc", parent=center, fontName="Helvetica-Bold", fontSize=14)
    ul_c    = ParagraphStyle("uc", parent=center, fontName="Helvetica-Bold",
                              fontSize=11, underline=True)
    normal  = S["Normal"]

    story = [
        Paragraph("Government of Nepal", center),
        Spacer(1, .15*cm),
        Paragraph(f"<b>{ctx.get('ministry_name','Ministry of Home Affairs')}</b>", bold_c),
        Spacer(1, .2*cm),
        Paragraph(ctx.get('address', 'Singhadurbar, Kathmandu, Nepal').replace('\n','<br/>'), right),
        Spacer(1, .6*cm),
        HRFlowable(width="100%", thickness=.5, color=colors.grey),
        Spacer(1, .5*cm),
        Paragraph(f"<b><u>{ctx.get('title','Notice')}</u></b>", center),
        Spacer(1, .2*cm),
        Paragraph(f"Date: {ctx.get('date','')}", center),
        Spacer(1, .6*cm),
        Paragraph(ctx.get('body','').replace('\n','<br/>'), normal),
    ]
    doc.build(story)
    return buf.getvalue()


def _job_pdf_fallback(ctx: dict) -> bytes:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib import colors
    from reportlab.lib.units import cm
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
                            topMargin=2*cm, bottomMargin=2*cm,
                            leftMargin=3*cm, rightMargin=2.5*cm)
    S = getSampleStyleSheet()
    center = ParagraphStyle("c",  parent=S["Normal"], alignment=TA_CENTER)
    right  = ParagraphStyle("r",  parent=S["Normal"], alignment=TA_RIGHT, fontSize=9)
    bold_c = ParagraphStyle("bc", parent=center, fontName="Helvetica-Bold", fontSize=14)
    normal = S["Normal"]

    story = [
        Paragraph("Government of Nepal", center),
        Spacer(1, .15*cm),
        Paragraph(f"<b>{ctx.get('department','Ministry of Home Affairs')}</b>", bold_c),
        Spacer(1, .2*cm),
        Paragraph(ctx.get('location','Kathmandu, Nepal').replace('\n','<br/>'), right),
        Spacer(1, .6*cm),
        HRFlowable(width="100%", thickness=.5, color=colors.grey),
        Spacer(1, .5*cm),
        Paragraph(f"<b><u>{ctx.get('title','Job Listing')}</u></b>", center),
        Spacer(1, .2*cm),
        Paragraph(f"Date: {ctx.get('date','')}", center),
        Spacer(1, .6*cm),
        Paragraph(ctx.get('description','').replace('\n','<br/>'), normal),
        Spacer(1, .3*cm),
        Paragraph(f"<b>Requirements:</b> {ctx.get('requirements','')}", normal),
        Paragraph(f"<b>Age Requirement:</b> {ctx.get('age_requirement','')}", normal),
        Paragraph(f"<b>Deadline:</b> {ctx.get('deadline','')}", normal),
        Spacer(1, .4*cm),
        Paragraph(f"<b>Contact:</b> {ctx.get('contact','').replace(chr(10),'<br/>')}", normal),
    ]
    doc.build(story)
    return buf.getvalue()


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def generate_notice_docx(context: dict) -> bytes:
    """
    Generate a Notice DOCX via docxtpl.
    TODO (DB integration): pass notice model fields as context.
    """
    tpl_path = _notice_template_path()
    if not os.path.exists(tpl_path):
        _build_notice_template(tpl_path)
    return _render_docx(tpl_path, context)


def generate_notice_pdf(context: dict) -> bytes:
    """
    Generate a Notice PDF:
      1. Render DOCX via docxtpl
      2. Convert with LibreOffice headless
      3. Fall back to reportlab if LibreOffice unavailable/fails
    TODO (DB integration): pass notice model fields as context.
    """
    try:
        docx_bytes = generate_notice_docx(context)
        pdf = _libreoffice_pdf(docx_bytes)
        if pdf:
            return pdf
    except Exception:
        pass
    return _notice_pdf_fallback(context)


def generate_job_docx(context: dict) -> bytes:
    """
    Generate a Job Listing DOCX via docxtpl.
    TODO (DB integration): pass job model fields as context.
    """
    tpl_path = _job_template_path()
    if not os.path.exists(tpl_path):
        _build_job_template(tpl_path)
    return _render_docx(tpl_path, context)


def generate_job_pdf(context: dict) -> bytes:
    """
    Generate a Job Listing PDF.
    TODO (DB integration): pass job model fields as context.
    """
    try:
        docx_bytes = generate_job_docx(context)
        pdf = _libreoffice_pdf(docx_bytes)
        if pdf:
            return pdf
    except Exception:
        pass
    return _job_pdf_fallback(context)
