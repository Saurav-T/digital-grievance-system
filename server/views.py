import io
import json
from datetime import timedelta
from functools import wraps

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.db.models import Count
from django.db.models.functions import TruncMonth
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from client.models import (
    Category, Grievance, GrievanceStatusHistory, JobListing, Notice, User,
)


# ─────────────────────────────────────────────
# Auth helpers
# ─────────────────────────────────────────────

def staff_required(fn):
    @wraps(fn)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated or not request.user.is_staff:
            return redirect("admin_panel:login")
        return fn(request, *args, **kwargs)
    return wrapper


def admin_login(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect("admin_panel:dashboard")
    if request.method == "POST":
        user = authenticate(request,
                            username=request.POST.get("email"),
                            password=request.POST.get("password"))
        if user and user.is_staff:
            login(request, user)
            return redirect("admin_panel:dashboard")
        messages.error(request, "Invalid credentials or insufficient permissions.")
    return render(request, "server/login.html", _ctx("login"))


def admin_logout(request):
    logout(request)
    return redirect("admin_panel:login")


# ─────────────────────────────────────────────
# Dashboard
# ─────────────────────────────────────────────

@staff_required
def dashboard(request):
    now = timezone.now()
    stats = {
        "total_complaints":       Grievance.objects.count(),
        "complaints_this_month":  Grievance.objects.filter(
            created_at__year=now.year, created_at__month=now.month).count(),
        "total_notices":  Notice.objects.count(),
        "active_users":   User.objects.filter(is_active=True).count(),
        "job_listings":   JobListing.objects.filter(is_active=True).count(),
    }

    recent_grievances = (
        Grievance.objects.select_related("user", "category").order_by("-created_at")[:5]
    )
    latest_notices = Notice.objects.order_by("-created_at")[:3]

    # Pie chart – grievance status
    status_data = {
        "Pending":   Grievance.objects.filter(status="Pending").count(),
        "In Review": Grievance.objects.filter(status="In Review").count(),
        "Resolved":  Grievance.objects.filter(status="Resolved").count(),
        "Rejected":  Grievance.objects.filter(status="Rejected").count(),
    }

    # Line chart – monthly trend (last 12 months)
    since = now - timedelta(days=365)
    monthly_qs = (
        Grievance.objects.filter(created_at__gte=since)
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(count=Count("id"))
        .order_by("month")
    )
    monthly_labels = [item["month"].strftime("%b %Y") for item in monthly_qs]
    monthly_counts = [item["count"] for item in monthly_qs]

    return render(request, "server/dashboard.html", _ctx(
        "dashboard",
        stats=stats,
        recent_grievances=recent_grievances,
        latest_notices=latest_notices,
        status_chart_data=json.dumps(status_data),
        monthly_labels=json.dumps(monthly_labels),
        monthly_counts=json.dumps(monthly_counts),
    ))


# ─────────────────────────────────────────────
# Users
# ─────────────────────────────────────────────

@staff_required
def users(request):
    if request.method == "POST":
        action = request.POST.get("action")
        try:
            if action == "add":
                User.objects.create_user(
                    email=request.POST["email"],
                    password=request.POST["password"],
                    first_name=request.POST["first_name"],
                    last_name=request.POST["last_name"],
                    phone_number=request.POST.get("phone_number", ""),
                    is_staff=request.POST.get("is_staff") == "on",
                    is_active=request.POST.get("is_active", "on") == "on",
                )
                messages.success(request, "User created successfully.")

            elif action == "edit":
                u = get_object_or_404(User, pk=request.POST["user_id"])
                u.first_name   = request.POST["first_name"]
                u.last_name    = request.POST["last_name"]
                u.email        = request.POST["email"]
                u.phone_number = request.POST.get("phone_number", "")
                u.is_staff     = request.POST.get("is_staff") == "on"
                u.is_active    = request.POST.get("is_active", "on") == "on"
                if request.POST.get("password"):
                    u.set_password(request.POST["password"])
                u.save()
                messages.success(request, "User updated successfully.")

            elif action == "delete":
                u = get_object_or_404(User, pk=request.POST["user_id"])
                u.delete()
                messages.success(request, "User deleted successfully.")

        except Exception as exc:
            messages.error(request, f"Error: {exc}")
        return redirect("admin_panel:users")

    all_users = User.objects.order_by("-date_joined")
    return render(request, "server/users.html", _ctx("users", users=all_users))


def user_json(request, pk):
    """Return user data as JSON for the edit modal."""
    u = get_object_or_404(User, pk=pk)
    return JsonResponse({
        "id": u.id,
        "first_name": u.first_name,
        "last_name": u.last_name,
        "email": u.email,
        "phone_number": u.phone_number,
        "is_staff": u.is_staff,
        "is_active": u.is_active,
    })


# ─────────────────────────────────────────────
# Categories
# ─────────────────────────────────────────────

@staff_required
def categories(request):
    if request.method == "POST":
        action = request.POST.get("action")
        try:
            if action == "add":
                Category.objects.create(
                    name=request.POST["name"],
                    description=request.POST.get("description", ""),
                )
                messages.success(request, "Category created.")

            elif action == "edit":
                cat = get_object_or_404(Category, pk=request.POST["cat_id"])
                cat.name        = request.POST["name"]
                cat.description = request.POST.get("description", "")
                cat.save()
                messages.success(request, "Category updated.")

            elif action == "delete":
                cat = get_object_or_404(Category, pk=request.POST["cat_id"])
                cat.delete()
                messages.success(request, "Category deleted.")

        except Exception as exc:
            messages.error(request, f"Error: {exc}")
        return redirect("admin_panel:categories")

    all_cats = Category.objects.annotate(grievance_count=Count("grievances")).order_by("name")
    return render(request, "server/categories.html", _ctx("categories", categories=all_cats))


def category_json(request, pk):
    cat = get_object_or_404(Category, pk=pk)
    return JsonResponse({"id": cat.id, "name": cat.name, "description": cat.description or ""})


# ─────────────────────────────────────────────
# Grievances
# ─────────────────────────────────────────────

@staff_required
def grievances(request):
    if request.method == "POST":
        action     = request.POST.get("action")
        g_id       = request.POST.get("grievance_id")
        grievance  = get_object_or_404(Grievance, pk=g_id) if g_id else None
        try:
            if action == "resolve":
                note = request.POST.get("resolution_note", "").strip()
                grievance.status          = "Resolved"
                grievance.resolution_note = note
                grievance.resolved_at     = timezone.now()
                grievance.save()
                GrievanceStatusHistory.objects.create(
                    grievance=grievance, status="Resolved",
                    remarks=note, updated_by=request.user)
                messages.success(request, f"Grievance #{grievance.id} resolved.")

            elif action == "reject":
                reason = request.POST.get("rejection_reason", "").strip()
                grievance.status          = "Rejected"
                grievance.resolution_note = reason
                grievance.rejected_at     = timezone.now()
                grievance.save()
                GrievanceStatusHistory.objects.create(
                    grievance=grievance, status="Rejected",
                    remarks=reason, updated_by=request.user)
                messages.success(request, f"Grievance #{grievance.id} rejected.")

            elif action == "edit":
                grievance.subject     = request.POST["subject"]
                grievance.description = request.POST["description"]
                grievance.priority    = request.POST["priority"]
                cat_id = request.POST.get("category")
                grievance.category    = Category.objects.filter(pk=cat_id).first() if cat_id else None
                old_status = grievance.status
                new_status = request.POST.get("status", old_status)
                if new_status != old_status:
                    grievance.status = new_status
                    GrievanceStatusHistory.objects.create(
                        grievance=grievance, status=new_status,
                        remarks="Updated via admin panel", updated_by=request.user)
                grievance.save()
                messages.success(request, "Grievance updated.")

            elif action == "mark_spam":
                grievance.is_spam    = True
                grievance.spam_score = 100.0
                grievance.save()
                messages.success(request, "Marked as spam.")

            elif action == "delete":
                grievance.delete()
                messages.success(request, "Grievance deleted.")

        except Exception as exc:
            messages.error(request, f"Error: {exc}")
        return redirect("admin_panel:grievances")

    qs = (Grievance.objects
          .select_related("user", "category")
          .order_by("-created_at"))

    # Simple filters
    status_filter   = request.GET.get("status", "")
    priority_filter = request.GET.get("priority", "")
    if status_filter:
        qs = qs.filter(status=status_filter)
    if priority_filter:
        qs = qs.filter(priority=priority_filter)

    return render(request, "server/grievances.html", _ctx(
        "grievances",
        grievances=qs,
        categories=Category.objects.all(),
        status_choices=Grievance.STATUS_CHOICES,
        priority_choices=Grievance.PRIORITY_CHOICES,
        status_filter=status_filter,
        priority_filter=priority_filter,
    ))


def grievance_json(request, pk):
    """Full detail JSON used by the View modal."""
    g = get_object_or_404(Grievance.objects.select_related("user", "category"), pk=pk)
    history = g.status_history.select_related("updated_by").order_by("updated_at")
    return JsonResponse({
        "id":              g.id,
        "subject":         g.subject,
        "description":     g.description,
        "user":            g.user.get_full_name(),
        "user_email":      g.user.email,
        "category":        g.category.name if g.category else "—",
        "priority":        g.priority,
        "priority_colour": g.priority_colour,
        "status":          g.status,
        "status_colour":   g.status_colour,
        "location_url":    g.location_url or "",
        "attachment":      g.attachment.url if g.attachment else "",
        "is_spam":         g.is_spam,
        "spam_score":      round(g.spam_score, 1),
        "resolution_note": g.resolution_note or "",
        "created_at":      g.created_at.strftime("%d %b %Y, %I:%M %p"),
        "resolved_at":     g.resolved_at.strftime("%d %b %Y, %I:%M %p") if g.resolved_at else "",
        "rejected_at":     g.rejected_at.strftime("%d %b %Y, %I:%M %p") if g.rejected_at else "",
        "timeline": [
            {
                "status":     h.status,
                "remarks":    h.remarks or "",
                "updated_by": h.updated_by.get_full_name() if h.updated_by else "System",
                "updated_at": h.updated_at.strftime("%d %b %Y, %I:%M %p"),
            }
            for h in history
        ],
    })


def grievance_pdf(request, pk):
    """Generate a PDF report for a grievance using ReportLab."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import (HRFlowable, Paragraph, SimpleDocTemplate,
                                        Spacer, Table, TableStyle)
    except ImportError:
        messages.error(request, "PDF requires: pip install reportlab")
        return redirect("admin_panel:grievances")

    g = get_object_or_404(Grievance.objects.select_related("user", "category"), pk=pk)
    history = g.status_history.select_related("updated_by").order_by("updated_at")

    buf    = io.BytesIO()
    doc    = SimpleDocTemplate(buf, pagesize=A4,
                               topMargin=2*cm, bottomMargin=2*cm,
                               leftMargin=2.5*cm, rightMargin=2.5*cm)
    styles = getSampleStyleSheet()
    bold   = ParagraphStyle("bold", parent=styles["Normal"], fontName="Helvetica-Bold")
    story  = []

    # Title
    story.append(Paragraph(f"Grievance Report — #{g.id}", styles["Title"]))
    story.append(Spacer(1, 0.4*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
    story.append(Spacer(1, 0.4*cm))

    # Meta table
    meta = [
        ["Subject",    g.subject],
        ["Submitted By", g.user.get_full_name() + f" ({g.user.email})"],
        ["Category",   g.category.name if g.category else "—"],
        ["Priority",   g.priority],
        ["Status",     g.status],
        ["Date Filed", g.created_at.strftime("%d %b %Y, %I:%M %p")],
        ["Spam Score", f"{g.spam_score:.1f}%"],
    ]
    tbl = Table([[Paragraph(r[0], bold), Paragraph(r[1], styles["Normal"])] for r in meta],
                colWidths=[4*cm, 12.5*cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (0,-1), colors.HexColor("#dbeafe")),
        ("GRID", (0,0), (-1,-1), 0.4, colors.lightgrey),
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("PADDING", (0,0), (-1,-1), 5),
    ]))
    story += [tbl, Spacer(1, 0.6*cm)]

    # Description
    story.append(Paragraph("Description", bold))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(g.description.replace("\n", "<br/>"), styles["Normal"]))
    story.append(Spacer(1, 0.5*cm))

    # Resolution
    if g.resolution_note:
        story.append(Paragraph("Resolution / Rejection Note", bold))
        story.append(Spacer(1, 0.2*cm))
        story.append(Paragraph(g.resolution_note.replace("\n", "<br/>"), styles["Normal"]))
        story.append(Spacer(1, 0.5*cm))

    # Location
    if g.location_url:
        story.append(Paragraph("Location URL", bold))
        story.append(Paragraph(g.location_url, styles["Normal"]))
        story.append(Spacer(1, 0.5*cm))

    # Timeline
    if history.exists():
        story.append(Paragraph("Status Timeline", bold))
        story.append(Spacer(1, 0.2*cm))
        for h in history:
            by = h.updated_by.get_full_name() if h.updated_by else "System"
            line = f"<b>{h.status}</b> — {h.updated_at.strftime('%d %b %Y %I:%M %p')} by {by}"
            if h.remarks:
                line += f"<br/><i>{h.remarks}</i>"
            story.append(Paragraph(line, styles["Normal"]))
            story.append(Spacer(1, 0.15*cm))

    doc.build(story)
    buf.seek(0)
    resp = HttpResponse(buf, content_type="application/pdf")
    resp["Content-Disposition"] = f'attachment; filename="grievance_{g.id}.pdf"'
    return resp


# ─────────────────────────────────────────────
# Notices
# ─────────────────────────────────────────────

@staff_required
def notices(request):
    if request.method == "POST":
        action = request.POST.get("action")
        try:
            if action == "add":
                n = Notice(
                    title=request.POST["title"],
                    description=request.POST["description"],
                    issue_date=request.POST["issue_date"],
                    created_by=request.user,
                )
                if "image" in request.FILES:
                    n.image = request.FILES["image"]
                n.save()
                messages.success(request, "Notice created.")

            elif action == "edit":
                n = get_object_or_404(Notice, pk=request.POST["notice_id"])
                n.title       = request.POST["title"]
                n.description = request.POST["description"]
                n.issue_date  = request.POST["issue_date"]
                if "image" in request.FILES:
                    n.image = request.FILES["image"]
                n.save()
                messages.success(request, "Notice updated.")

            elif action == "delete":
                n = get_object_or_404(Notice, pk=request.POST["notice_id"])
                n.delete()
                messages.success(request, "Notice deleted.")

        except Exception as exc:
            messages.error(request, f"Error: {exc}")
        return redirect("admin_panel:notices")

    all_notices = Notice.objects.select_related("created_by").order_by("-created_at")
    return render(request, "server/notices.html", _ctx("notices", notices=all_notices))


def notice_json(request, pk):
    n = get_object_or_404(Notice, pk=pk)
    return JsonResponse({
        "id":          n.id,
        "title":       n.title,
        "description": n.description,
        "issue_date":  n.issue_date.strftime("%Y-%m-%dT%H:%M") if n.issue_date else "",
        "image":       n.image.url if n.image else "",
        "created_by":  n.created_by.get_full_name() if n.created_by else "—",
    })


# ─────────────────────────────────────────────
# Job Listings
# ─────────────────────────────────────────────

@staff_required
def jobs(request):
    if request.method == "POST":
        action = request.POST.get("action")
        try:
            if action == "add":
                JobListing.objects.create(
                    job_title=request.POST["job_title"],
                    department=request.POST["department"],
                    department_location=request.POST["department_location"],
                    issue_date=request.POST["issue_date"],
                    deadline=request.POST["deadline"],
                    job_description=request.POST["job_description"],
                    age_requirement=request.POST.get("age_requirement", ""),
                    job_requirements=request.POST["job_requirements"],
                    contact_information=request.POST["contact_information"],
                    is_active=True,
                    created_by=request.user,
                )
                messages.success(request, "Job listing created.")

            elif action == "edit":
                j = get_object_or_404(JobListing, pk=request.POST["job_id"])
                j.job_title           = request.POST["job_title"]
                j.department          = request.POST["department"]
                j.department_location = request.POST["department_location"]
                j.issue_date          = request.POST["issue_date"]
                j.deadline            = request.POST["deadline"]
                j.job_description     = request.POST["job_description"]
                j.age_requirement     = request.POST.get("age_requirement", "")
                j.job_requirements    = request.POST["job_requirements"]
                j.contact_information = request.POST["contact_information"]
                j.save()
                messages.success(request, "Job listing updated.")

            elif action == "close":
                j = get_object_or_404(JobListing, pk=request.POST["job_id"])
                j.is_active = False
                j.save()
                messages.success(request, "Job closed.")

            elif action == "delete":
                j = get_object_or_404(JobListing, pk=request.POST["job_id"])
                j.delete()
                messages.success(request, "Job listing deleted.")

        except Exception as exc:
            messages.error(request, f"Error: {exc}")
        return redirect("admin_panel:jobs")

    all_jobs = JobListing.objects.select_related("created_by").order_by("-created_at")
    return render(request, "server/jobs.html", _ctx("jobs", jobs=all_jobs))


def job_json(request, pk):
    j = get_object_or_404(JobListing, pk=pk)
    return JsonResponse({
        "id":                   j.id,
        "job_title":            j.job_title,
        "department":           j.department,
        "department_location":  j.department_location,
        "issue_date":           j.issue_date.strftime("%Y-%m-%d"),
        "deadline":             j.deadline.strftime("%Y-%m-%d"),
        "job_description":      j.job_description,
        "age_requirement":      j.age_requirement,
        "job_requirements":     j.job_requirements,
        "contact_information":  j.contact_information,
        "is_active":            j.is_active,
    })


# ─────────────────────────────────────────────
# Context helpers (sidebar nav injected to every view)
# ─────────────────────────────────────────────

_NAV = [
    ("Dashboard",   "/admin-panel/",              "dashboard"),
    ("Users",       "/admin-panel/users/",         "users"),
    ("Categories",  "/admin-panel/categories/",    "categories"),
    ("Grievances",  "/admin-panel/grievances/",    "grievances"),
    ("Notices",     "/admin-panel/notices/",       "notices"),
    ("Jobs",        "/admin-panel/jobs/",          "jobs"),
]


def _ctx(active, **extra):
    return {"active": active, "sidebar_nav": _NAV, **extra}
