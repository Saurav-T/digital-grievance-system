"""
client/generators.py
────────────────────
Two independent, lightweight renderers — no LibreOffice, no office suite:

- DOCX (for download) is rendered from a FIXED, hand-designed Word template
  via docxtpl.
- PDF (for preview/print) is rendered straight from an HTML/CSS template
  via WeasyPrint — it is NOT a conversion of the DOCX.

The DOCX templates are NOT built by this file — you design them yourself in
Word / LibreOffice Writer and drop them at:

    media/docx_templates/notice_template.docx
    media/docx_templates/job_template.docx

The PDF templates live at:

    client/templates/client/pdf/notice_pdf.html
    client/templates/client/pdf/job_pdf.html

Style each one independently — they just need to carry the same branding,
not be byte-for-byte identical.

Anywhere you want dynamic text in those templates, type a Jinja
placeholder as plain text, e.g. {{ title }}, {{ date }}, {{ body }}.

For the logo: don't paste an image into the template. Instead type the
placeholder {{ logo }} wherever you want the logo to appear (usually the
header). At render time this file swaps that placeholder for a real
image, sized exactly as configured in LOGO_WIDTH_MM below — that's the
only way to control an inserted image's size dynamically with docxtpl.

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
import logging
import os

from django.conf import settings

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Logo configuration
# ─────────────────────────────────────────────────────────────────────────────

# Path to the logo image used to fill in the {{ logo }} placeholder.
# Point this at whichever file you want — the static emblem, or something
# in media/ if you want it editable without a redeploy.
LOGO_PATH = os.path.join(settings.BASE_DIR, "client", "static", "client", "img", "emblem.png")

# Custom size for the inserted logo. Only ONE of width/height needs to be
# set for the aspect ratio to be preserved automatically by docxtpl/python-docx
# — but you can set both if you want to force an exact box.
LOGO_WIDTH_MM = 25   # ← change this to resize the logo everywhere at once
LOGO_HEIGHT_MM = None  # leave as None to keep aspect ratio


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


def _require_template(path: str, label: str) -> None:
    """Fail loudly (instead of silently generating a placeholder doc) if the
    person hasn't dropped their fixed template file in place yet."""
    if not os.path.exists(path):
        raise FileNotFoundError(
            f"{label} template not found at {path}. "
            f"Design it in Word/LibreOffice and save it there — "
            f"see the docstring at the top of client/generators.py."
        )


def _build_logo_image(tpl):
    """Returns an InlineImage bound to `tpl`, sized per LOGO_WIDTH_MM /
    LOGO_HEIGHT_MM above. Returns None (and logs) if the logo file is missing,
    so a missing logo never breaks document generation — the {{ logo }}
    placeholder text just won't be replaced."""
    from docxtpl import InlineImage
    from docx.shared import Mm

    if not os.path.exists(LOGO_PATH):
        return None

    kwargs = {}
    if LOGO_WIDTH_MM:
        kwargs["width"] = Mm(LOGO_WIDTH_MM)
    if LOGO_HEIGHT_MM:
        kwargs["height"] = Mm(LOGO_HEIGHT_MM)

    return InlineImage(tpl, LOGO_PATH, **kwargs)


# ─── DOCX rendering via docxtpl ──────────────────────────────────────────────

def _render_docx(template_path: str, context: dict) -> bytes:
    """Render a docxtpl template (fixed, hand-designed) and return DOCX bytes.
    Automatically injects a sized `logo` InlineImage into the context so any
    template containing {{ logo }} picks it up without the caller having to
    remember to pass it."""
    from docxtpl import DocxTemplate

    tpl = DocxTemplate(template_path)

    full_context = dict(context)
    full_context.setdefault("logo", _build_logo_image(tpl))

    tpl.render(full_context)
    buf = io.BytesIO()
    tpl.save(buf)
    return buf.getvalue()


# ─── PDF generation: WeasyPrint (HTML/CSS → PDF, no LibreOffice needed) ─────
# The PDF is rendered independently from a small HTML template (see
# client/templates/client/pdf/notice_pdf.html and job_pdf.html) rather than
# by converting the .docx. This means: no LibreOffice subprocess, no ~600MB
# office suite in your deployment image, no conversion startup lag, and no
# silent failures from sandboxed/no-HOME server environments.
#
# You style the DOCX (for downloads) in Word, and the PDF (for
# preview/print) in the HTML/CSS templates — they don't have to be
# byte-for-byte identical, just carry the same branding.

def _logo_file_uri() -> str:
    """file:// URI WeasyPrint can load directly, or '' if the logo is missing."""
    if not os.path.exists(LOGO_PATH):
        return ""
    return "file://" + LOGO_PATH.replace(os.sep, "/")


def _render_pdf_from_html(template_name: str, context: dict) -> bytes:
    from django.template.loader import render_to_string
    from weasyprint import HTML

    full_context = dict(context)
    full_context.setdefault("logo_url", _logo_file_uri())

    html_string = render_to_string(template_name, full_context)
    return HTML(string=html_string).write_pdf()


# ─────────────────────────────────────────────────────────────────────────────
# Public API
# ─────────────────────────────────────────────────────────────────────────────

def generate_notice_docx(context: dict) -> bytes:
    """
    Generate a Notice DOCX from the fixed template you designed at
    media/docx_templates/notice_template.docx.
    TODO (DB integration): pass notice model fields as context.
    """
    tpl_path = _notice_template_path()
    _require_template(tpl_path, "Notice")
    return _render_docx(tpl_path, context)


def generate_notice_pdf(context: dict) -> bytes:
    """
    Generate a Notice PDF directly from the HTML template — independent of
    the DOCX / LibreOffice entirely.
    TODO (DB integration): pass notice model fields as context.
    """
    return _render_pdf_from_html("client/pdf/notice_pdf.html", context)


def generate_job_docx(context: dict) -> bytes:
    """
    Generate a Job Listing DOCX from the fixed template you designed at
    media/docx_templates/job_template.docx.
    TODO (DB integration): pass job model fields as context.
    """
    tpl_path = _job_template_path()
    _require_template(tpl_path, "Job listing")
    return _render_docx(tpl_path, context)


def generate_job_pdf(context: dict) -> bytes:
    """
    Generate a Job Listing PDF directly from the HTML template — independent
    of the DOCX / LibreOffice entirely.
    TODO (DB integration): pass job model fields as context.
    """
    return _render_pdf_from_html("client/pdf/job_pdf.html", context)