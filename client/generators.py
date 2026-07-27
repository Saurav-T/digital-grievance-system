"""
client/generators.py
────────────────────
Two independent, lightweight renderers — no LibreOffice, no office suite:

- DOCX (for download) is rendered from a FIXED, hand-designed Word template
  via docxtpl.
- PDF (for preview/print) is rendered straight from an HTML/CSS template
  via xhtml2pdf — it is NOT a conversion of the DOCX.

The DOCX templates are NOT built by this file — you design them yourself in
Word / LibreOffice Writer and drop them at:

    media/docx_templates/notice_template.docx
    media/docx_templates/job_template.docx

The PDF templates live at:

    client/templates/client/pdf/notice_pdf.html
    client/templates/client/pdf/job_pdf.html

Style each one independently — they just need to carry the same branding,
not be byte-for-byte identical. Note that xhtml2pdf only understands a
subset of CSS 2.1 (no flexbox/grid, limited <hr>/white-space support), so
those two templates are written conservatively — plain block/table layout,
inline styles kept simple. If you redesign them, keep that in mind.

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


# ─── PDF generation: xhtml2pdf (HTML/CSS → PDF, no system libraries) ────────
# The PDF is rendered independently from a small HTML template (see
# client/templates/client/pdf/notice_pdf.html and job_pdf.html) rather than
# by converting the .docx. xhtml2pdf is pure Python, built on top of
# ReportLab — there's no Cairo/Pango/GDK-Pixbuf to install at the OS level,
# no subprocess, and it works fine in minimal/sandboxed server environments.
#
# You style the DOCX (for downloads) in Word, and the PDF (for
# preview/print) in the HTML/CSS templates — they don't have to be
# byte-for-byte identical, just carry the same branding.
#
# Trade-off vs WeasyPrint: xhtml2pdf only supports a subset of CSS 2.1
# (no flexbox/grid; @page margin rules work but are simpler; things like
# `white-space: pre-line` aren't reliable — templates use `linebreaksbr`
# in Django instead). See the two pdf/*.html templates for the patterns
# that render correctly.

def _logo_file_uri() -> str:
    """file:// URI for the logo, or '' if the logo is missing. Resolved back
    to a real filesystem path by _link_callback() below at render time."""
    if not os.path.exists(LOGO_PATH):
        return ""
    return "file://" + LOGO_PATH.replace(os.sep, "/")


# ─── Unicode font (optional) ─────────────────────────────────────────────
# xhtml2pdf's built-in Helvetica only covers Latin text. DejaVu Sans adds
# Devanagari/wider Unicode coverage for things like Nepali names — but it's
# an OS-level font, not something we ship, so its location varies (it's at
# /usr/share/fonts/truetype/dejavu/... in the Docker image via
# `apt-get install fonts-dejavu`, but usually isn't present at all on a
# bare macOS/Windows dev machine running `manage.py runserver` directly).
#
# IMPORTANT: never hardcode a single path here — if it doesn't exist on
# whichever machine is running the code, xhtml2pdf raises while parsing
# @font-face and the whole PDF request crashes with a 500. Instead we
# probe a handful of common locations and only tell the template about a
# font-face rule when a real file was found; otherwise the PDF templates
# just render with Helvetica, which always works.
_DEJAVU_REGULAR_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",      # Debian/Ubuntu (this project's Dockerfile)
    "/usr/share/fonts/dejavu/DejaVuSans.ttf",                # some RPM-based distros
    "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf",     # Fedora/RHEL
    "/opt/homebrew/share/fonts/DejaVuSans.ttf",              # Homebrew on Apple Silicon
    "/usr/local/share/fonts/DejaVuSans.ttf",                 # Homebrew on Intel Mac / manual install
    "C:\\Windows\\Fonts\\DejaVuSans.ttf",                    # Windows, if manually installed
]
_DEJAVU_BOLD_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans-Bold.ttf",
    "/opt/homebrew/share/fonts/DejaVuSans-Bold.ttf",
    "/usr/local/share/fonts/DejaVuSans-Bold.ttf",
    "C:\\Windows\\Fonts\\DejaVuSans-Bold.ttf",
]


def _first_existing(paths):
    for path in paths:
        if os.path.isfile(path):
            return path
    return None


def _pdf_font_context() -> dict:
    """Returns absolute filesystem paths (already forward-slashed, no URI
    scheme) for the templates to use in @font-face, or empty strings when
    DejaVu isn't available anywhere — in which case the templates fall back
    to Helvetica and nothing breaks."""
    regular = _first_existing(_DEJAVU_REGULAR_CANDIDATES)
    bold = _first_existing(_DEJAVU_BOLD_CANDIDATES)
    return {
        "pdf_font_regular": regular.replace(os.sep, "/") if regular else "",
        "pdf_font_bold": bold.replace(os.sep, "/") if bold else "",
    }


def _link_callback(uri: str, rel: str) -> str:
    """xhtml2pdf/ReportLab can't fetch http(s) or file:// URIs on their own —
    every <img src="..."> (and CSS url(...)) has to be resolved to a real,
    absolute path on disk before rendering. This is the standard xhtml2pdf
    pattern for that: handle our own file:// logo URIs, plus anything
    served from MEDIA_URL or STATIC_URL, and reject everything else so a
    stray external URL fails loudly instead of silently producing a blank
    image."""
    if uri.startswith("file://"):
        path = uri[len("file://"):]
        # file:///C:/... on Windows leaves a leading slash before the drive
        # letter — strip it so os.path checks work.
        if os.name == "nt" and path.startswith("/") and ":" in path:
            path = path.lstrip("/")
        return path

    if uri.startswith(settings.MEDIA_URL):
        path = os.path.join(settings.MEDIA_ROOT, uri[len(settings.MEDIA_URL):])
    elif uri.startswith(settings.STATIC_URL):
        # No STATIC_ROOT is configured in settings.py (dev-only static
        # serving), so fall back to each app's static/ dir the same way
        # Django's staticfiles finders would.
        candidate = os.path.join(settings.BASE_DIR, "client", "static", uri[len(settings.STATIC_URL):])
        path = candidate
    else:
        # Absolute filesystem path already, or something we don't recognise
        # — hand it back unchanged rather than guessing.
        return uri

    if not os.path.isfile(path):
        logger.warning("PDF link_callback: could not resolve %r to a file (looked at %r)", uri, path)
        return uri

    return path


def _render_pdf_from_html(template_name: str, context: dict) -> bytes:
    from django.template.loader import render_to_string
    from xhtml2pdf import pisa

    full_context = dict(context)
    full_context.setdefault("logo_url", _logo_file_uri())
    full_context.update(_pdf_font_context())

    html_string = render_to_string(template_name, full_context)

    buf = io.BytesIO()
    try:
        result = pisa.CreatePDF(
            src=html_string,
            dest=buf,
            link_callback=_link_callback,
            encoding="utf-8",
        )
    except Exception as exc:
        # Never let a rendering hiccup (bad font, unreadable image, etc.)
        # bubble up as an opaque 500 — log the real cause so it's easy to
        # diagnose, then re-raise with a message that actually says what
        # template was involved.
        logger.exception("xhtml2pdf raised while rendering %s", template_name)
        raise RuntimeError(f"xhtml2pdf raised while rendering {template_name}: {exc}") from exc

    if result.err:
        raise RuntimeError(
            f"xhtml2pdf failed to render {template_name} "
            f"({result.err} error(s) — check server logs for details)."
        )
    return buf.getvalue()


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
    the DOCX entirely.
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
    of the DOCX entirely.
    TODO (DB integration): pass job model fields as context.
    """
    return _render_pdf_from_html("client/pdf/job_pdf.html", context)