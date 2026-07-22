import io
import json
import os
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
# Dashboard (Updated with carousel support)
# ─────────────────────────────────────────────

@staff_required
def dashboard(request):
    from datetime import timedelta
    now = timezone.now()

    # ── Stat cards ────────────────────────────────────────────────────────────
    stats = {
        "total_complaints": Grievance.objects.count(),
        "complaints_this_month": Grievance.objects.filter(
            created_at__year=now.year, created_at__month=now.month).count(),
        "total_notices": Notice.objects.count(),
        "active_users": User.objects.filter(is_active=True).count(),
        "job_listings": JobListing.objects.filter(is_active=True).count(),
    }

    # ── Charts ────────────────────────────────────────────────────────────────
    status_data = {
        "Pending": Grievance.objects.filter(status="Pending").count(),
        "In Review": Grievance.objects.filter(status="In Review").count(),
        "Resolved": Grievance.objects.filter(status="Resolved").count(),
        "Rejected": Grievance.objects.filter(status="Rejected").count(),
    }

    since = now - timedelta(days=365)
    monthly_qs = (
        Grievance.objects.filter(created_at__gte=since)
        .annotate(month=TruncMonth("created_at"))
        .values("month").annotate(count=Count("id")).order_by("month")
    )
    monthly_labels = [item["month"].strftime("%b %Y") for item in monthly_qs]
    monthly_counts = [item["count"] for item in monthly_qs]

    # ── Carousel images ───────────────────────────────────────────────────────
    try:
        from client.models import CarouselImage
        carousel_images = CarouselImage.objects.order_by("order", "-created_at")
    except Exception:
        carousel_images = []

    # ── Recent tables ─────────────────────────────────────────────────────────
    recent_grievances = (
        Grievance.objects.select_related("user", "category").order_by("-created_at")[:5]
    )
    latest_notices = Notice.objects.order_by("-created_at")[:3]

    return render(request, "server/dashboard.html", _ctx(
        "dashboard",
        stats=stats,
        carousel_images=carousel_images,
        recent_grievances=recent_grievances,
        latest_notices=latest_notices,
        status_chart_data=json.dumps(status_data),
        monthly_labels=json.dumps(monthly_labels),
        monthly_counts=json.dumps(monthly_counts),
    ))


# ─────────────────────────────────────────────
# Carousel CRUD
# ─────────────────────────────────────────────

@staff_required
def carousel_upload(request):
    """POST: upload a new carousel image (redirects back to dashboard)."""
    if request.method == "POST":
        try:
            from client.models import CarouselImage
            last = CarouselImage.objects.order_by("-order").first()
            next_order = (last.order + 1) if last else 1

            img = CarouselImage(
                image=request.FILES["image"],
                caption=request.POST.get("caption", ""),
                order=next_order,
                is_active=request.POST.get("is_active") == "on",
                created_by=request.user,
            )
            img.save()
            messages.success(request, "Carousel image uploaded successfully.")
        except Exception as exc:
            messages.error(request, f"Upload failed: {exc}")
    return redirect("admin_panel:dashboard")


@staff_required
def carousel_delete(request, pk):
    """POST: delete a carousel image and its file from disk."""
    if request.method == "POST":
        try:
            from client.models import CarouselImage
            img = get_object_or_404(CarouselImage, pk=pk)
            if img.image and os.path.isfile(img.image.path):
                os.remove(img.image.path)
            img.delete()
            messages.success(request, "Image removed from carousel.")
        except Exception as exc:
            messages.error(request, f"Error: {exc}")
    return redirect("admin_panel:dashboard")


@staff_required
@require_POST
def carousel_reorder(request):
    """POST (AJAX/JSON): save drag-and-drop image order."""
    try:
        from client.models import CarouselImage
        data = json.loads(request.body)
        for item in data.get("order", []):
            CarouselImage.objects.filter(pk=item["id"]).update(order=item["order"])
        return JsonResponse({"status": "ok"})
    except Exception as exc:
        return JsonResponse({"status": "error", "msg": str(exc)}, status=400)


@staff_required
def carousel_api(request):
    """GET: public JSON endpoint for the client-side hero carousel."""
    try:
        from client.models import CarouselImage
        images = CarouselImage.objects.filter(is_active=True).order_by("order")
        data = [
            {
                "id": img.id,
                "url": request.build_absolute_uri(img.image.url),
                "caption": img.caption,
                "order": img.order,
            }
            for img in images
        ]
    except Exception:
        data = []
    return JsonResponse({"images": data})


# ─────────────────────────────────────────────
# Admin Profile
# ─────────────────────────────────────────────

@staff_required
def admin_profile(request):
    """Admin's own profile page."""
    admin_user = request.user

    # ── Handle profile update POST ────────────────────────────────────────────
    if request.method == "POST" and request.POST.get("action") == "update_profile":
        try:
            admin_user.first_name = request.POST.get("first_name", admin_user.first_name)
            admin_user.last_name = request.POST.get("last_name", admin_user.last_name)
            admin_user.email = request.POST.get("email", admin_user.email)
            admin_user.phone_number = request.POST.get("phone_number", admin_user.phone_number)
            admin_user.save()
            messages.success(request, "Profile updated successfully.")
        except Exception as exc:
            messages.error(request, f"Error: {exc}")
        return redirect("admin_panel:admin_profile")

    # ── Admin activity stats ──────────────────────────────────────────────────
    admin_stats = [
        {
            "label": "Grievances Handled",
            "value": GrievanceStatusHistory.objects.filter(updated_by=admin_user).count(),
            "sub": None,
            "bg": "bg-blue-100", "color": "text-brand-blue",
            "icon_path": "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z",
        },
        {
            "label": "Notices Published",
            "value": Notice.objects.filter(created_by=admin_user).count(),
            "sub": None,
            "bg": "bg-purple-100", "color": "text-purple-600",
            "icon_path": "M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9",
        },
        {
            "label": "Jobs Posted",
            "value": JobListing.objects.filter(created_by=admin_user).count(),
            "sub": None,
            "bg": "bg-green-100", "color": "text-green-600",
            "icon_path": "M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m-4 6h16v8a2 2 0 01-2 2H6a2 2 0 01-2-2v-8z",
        },
        {
            "label": "Total Users",
            "value": User.objects.count(),
            "sub": f"Active: {User.objects.filter(is_active=True).count()}",
            "bg": "bg-orange-100", "color": "text-orange-600",
            "icon_path": "M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z",
        },
    ]

    # ── Overview fields ───────────────────────────────────────────────────────
    overview_fields = [
        {"label": "Full Name", "value": admin_user.get_full_name()},
        {"label": "Email", "value": admin_user.email},
        {"label": "Phone", "value": admin_user.phone_number or "—"},
        {"label": "Role", "value": "Superuser" if admin_user.is_superuser else "Staff Admin"},
        {"label": "Date Joined", "value": admin_user.date_joined.strftime("%d %B %Y")},
        {"label": "Last Login", "value": admin_user.last_login.strftime("%d %B %Y, %I:%M %p") if admin_user.last_login else "Never"},
        {"label": "Status", "value": "Active" if admin_user.is_active else "Inactive"},
    ]

    # ── System access permissions ─────────────────────────────────────────────
    permissions = [
        {"label": "Manage Users", "granted": admin_user.is_superuser or admin_user.is_staff,
         "bg": "bg-blue-100", "color": "text-brand-blue",
         "icon": "M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z"},
        {"label": "Manage Grievances", "granted": True,
         "bg": "bg-orange-100", "color": "text-orange-600",
         "icon": "M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"},
        {"label": "Publish Notices", "granted": True,
         "bg": "bg-purple-100", "color": "text-purple-600",
         "icon": "M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"},
        {"label": "Manage Job Listings", "granted": True,
         "bg": "bg-green-100", "color": "text-green-600",
         "icon": "M21 13.255A23.931 23.931 0 0112 15c-3.183 0-6.22-.62-9-1.745M16 6V4a2 2 0 00-2-2h-4a2 2 0 00-2 2v2m-4 6h16v8a2 2 0 01-2 2H6a2 2 0 01-2-2v-8z"},
        {"label": "System Configuration", "granted": admin_user.is_superuser,
         "bg": "bg-red-100", "color": "text-red-600",
         "icon": "M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z M15 12a3 3 0 11-6 0 3 3 0 016 0z"},
    ]

    # ── Activity chart data (demo) ────────────────────────────────────────────
    labels = ["Jan","Feb","Mar","Apr","May","Jun","Jul","Aug","Sep","Oct","Nov","Dec"]
    act_griev = [3, 5, 2, 8, 6, 4, 7, 9, 5, 6, 8, 4]
    act_notices = [1, 2, 1, 3, 2, 1, 2, 3, 2, 1, 2, 1]
    act_jobs = [0, 1, 0, 1, 2, 0, 1, 0, 1, 2, 1, 0]

    total_actions = sum(act_griev) + sum(act_notices) + sum(act_jobs)
    avg_actions = round(total_actions / 12)
    peak_idx = max(range(12), key=lambda i: act_griev[i] + act_notices[i] + act_jobs[i])
    peak_month = labels[peak_idx]

    # ── Notification settings ─────────────────────────────────────────────────
    admin_notif_settings = [
        {"key": "new_grievance", "label": "New Grievance Submitted", "desc": "Notify when a citizen submits a grievance.", "enabled": True},
        {"key": "status_change", "label": "Grievance Status Changed", "desc": "Notify when a grievance status is updated.", "enabled": True},
        {"key": "new_user", "label": "New User Registration", "desc": "Notify when a new user registers.", "enabled": False},
        {"key": "daily_summary", "label": "Daily Summary Email", "desc": "Receive a daily activity digest by email.", "enabled": True},
        {"key": "security_alert","label": "Security Alerts", "desc": "Notify on login from new device or location.", "enabled": True},
    ]

    return render(request, "server/admin_profile.html", _ctx(
        "admin_profile",
        admin_user=admin_user,
        admin_stats=admin_stats,
        overview_fields=overview_fields,
        permissions=permissions,
        activity_labels=json.dumps(labels),
        activity_grievances=json.dumps(act_griev),
        activity_notices=json.dumps(act_notices),
        activity_jobs=json.dumps(act_jobs),
        peak_month=peak_month,
        avg_actions=avg_actions,
        total_actions=total_actions,
        admin_notif_settings=admin_notif_settings,
    ))


# ─────────────────────────────────────────────
# Users, Categories, Grievances, Notices, Jobs
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
                    username=request.POST.get("username") or None,
                    phone_number=request.POST.get("phone_number", ""),
                    is_staff=request.POST.get("is_staff") == "on",
                    is_active=request.POST.get("is_active", "on") == "on",
                    user_type="Citizen",
                )
                messages.success(request, "User created successfully.")

            elif action == "edit":
                u = get_object_or_404(User, pk=request.POST["user_id"])
                u.first_name   = request.POST["first_name"]
                u.last_name    = request.POST["last_name"]
                u.email        = request.POST["email"]
                u.username     = request.POST.get("username") or u.username
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

            elif action == "add_admin":
                User.objects.create_user(
                    email=request.POST["email"],
                    password=request.POST["password"],
                    first_name=request.POST["first_name"],
                    last_name=request.POST["last_name"],
                    phone_number=request.POST.get("phone_number", ""),
                    is_staff=True,
                    is_superuser=request.POST.get("is_superuser") == "on",
                    is_active=request.POST.get("is_active", "on") == "on",
                    user_type="Staff",
                )
                messages.success(request, "Administrator created successfully.")

            elif action == "edit_admin":
                a = get_object_or_404(User, pk=request.POST["user_id"])
                a.first_name    = request.POST["first_name"]
                a.last_name     = request.POST["last_name"]
                a.email         = request.POST["email"]
                a.phone_number  = request.POST.get("phone_number", "")
                a.is_superuser  = request.POST.get("is_superuser") == "on"
                a.is_active     = request.POST.get("is_active", "on") == "on"
                if request.POST.get("password"):
                    a.set_password(request.POST["password"])
                a.save()
                messages.success(request, "Administrator updated successfully.")

            elif action == "delete_admin":
                a = get_object_or_404(User, pk=request.POST["user_id"])
                a.delete()
                messages.success(request, "Administrator deleted successfully.")

        except Exception as exc:
            messages.error(request, f"Error: {exc}")
        return redirect("admin_panel:users")

    all_users = User.objects.filter(is_staff=False).order_by("-date_joined")
    admins = User.objects.filter(is_staff=True).order_by("-date_joined")
    return render(request, "server/users.html", _ctx("users", users=all_users, admins=admins))


def user_json(request, pk):
    u = get_object_or_404(User, pk=pk)
    return JsonResponse({
        "id": u.id,
        "first_name": u.first_name,
        "last_name": u.last_name,
        "email": u.email,
        "username": u.username or "",
        "phone_number": u.phone_number,
        "is_staff": u.is_staff,
        "is_superuser": u.is_superuser,
        "is_active": u.is_active,
    })


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
    g = get_object_or_404(Grievance.objects.select_related("user", "category"), pk=pk)
    history = g.status_history.select_related("updated_by").order_by("updated_at")
    return JsonResponse({
        "id": g.id, "subject": g.subject, "description": g.description,
        "user": g.user.get_full_name(), "user_email": g.user.email,
        "category": g.category.name if g.category else "—",
        "priority": g.priority, "priority_colour": g.priority_colour,
        "status": g.status, "status_colour": g.status_colour,
        "location_url": g.location_url or "",
        "attachment": g.attachment.url if g.attachment else "",
        "is_spam": g.is_spam, "spam_score": round(g.spam_score, 1),
        "resolution_note": g.resolution_note or "",
        "created_at": g.created_at.strftime("%d %b %Y, %I:%M %p"),
        "resolved_at": g.resolved_at.strftime("%d %b %Y, %I:%M %p") if g.resolved_at else "",
        "rejected_at": g.rejected_at.strftime("%d %b %Y, %I:%M %p") if g.rejected_at else "",
        "timeline": [
            {
                "status": h.status,
                "remarks": h.remarks or "",
                "updated_by": h.updated_by.get_full_name() if h.updated_by else "System",
                "updated_at": h.updated_at.strftime("%d %b %Y, %I:%M %p"),
            }
            for h in history
        ],
    })


def grievance_pdf(request, pk):
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import cm
        from reportlab.platypus import HRFlowable, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except ImportError:
        messages.error(request, "PDF requires: pip install reportlab")
        return redirect("admin_panel:grievances")

    g = get_object_or_404(Grievance.objects.select_related("user", "category"), pk=pk)
    history = g.status_history.select_related("updated_by").order_by("updated_at")

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm,
                            leftMargin=2.5*cm, rightMargin=2.5*cm)
    styles = getSampleStyleSheet()
    bold = ParagraphStyle("bold", parent=styles["Normal"], fontName="Helvetica-Bold")
    story = []

    story.append(Paragraph(f"Grievance Report — #{g.id}", styles["Title"]))
    story.append(Spacer(1, 0.4*cm))
    story.append(HRFlowable(width="100%", thickness=1, color=colors.grey))
    story.append(Spacer(1, 0.4*cm))

    meta = [
        ["Subject", g.subject],
        ["Submitted By", g.user.get_full_name() + f" ({g.user.email})"],
        ["Category", g.category.name if g.category else "—"],
        ["Priority", g.priority],
        ["Status", g.status],
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

    story.append(Paragraph("Description", bold))
    story.append(Spacer(1, 0.2*cm))
    story.append(Paragraph(g.description.replace("\n", "<br/>"), styles["Normal"]))
    story.append(Spacer(1, 0.5*cm))

    if g.resolution_note:
        story.append(Paragraph("Resolution / Rejection Note", bold))
        story.append(Spacer(1, 0.2*cm))
        story.append(Paragraph(g.resolution_note.replace("\n", "<br/>"), styles["Normal"]))
        story.append(Spacer(1, 0.5*cm))

    if g.location_url:
        story.append(Paragraph("Location URL", bold))
        story.append(Paragraph(g.location_url, styles["Normal"]))
        story.append(Spacer(1, 0.5*cm))

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


@staff_required
def notices(request):
    if request.method == "POST":
        action = request.POST.get("action")
        try:
            if action == "add":
                n = Notice(
                    title=request.POST["title"],
                    description=request.POST["description"],
                    category=request.POST.get("category", "general"),
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
                n.category    = request.POST.get("category", n.category)
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
    return render(request, "server/notices.html", _ctx(
        "notices", notices=all_notices, category_choices=Notice.CATEGORY_CHOICES,
    ))


def notice_json(request, pk):
    n = get_object_or_404(Notice, pk=pk)
    return JsonResponse({
        "id": n.id, "title": n.title, "description": n.description,
        "category": n.category,
        "issue_date": n.issue_date.strftime("%Y-%m-%dT%H:%M") if n.issue_date else "",
        "image": n.image.url if n.image else "",
        "created_by": n.created_by.get_full_name() if n.created_by else "—",
    })


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
        "id": j.id, "job_title": j.job_title, "department": j.department,
        "department_location": j.department_location,
        "issue_date": j.issue_date.strftime("%Y-%m-%d"),
        "deadline": j.deadline.strftime("%Y-%m-%d"),
        "job_description": j.job_description,
        "age_requirement": j.age_requirement,
        "job_requirements": j.job_requirements,
        "contact_information": j.contact_information,
        "is_active": j.is_active,
    })


# ─────────────────────────────────────────────
# Context helper
# ─────────────────────────────────────────────

_NAV = [
    ("Dashboard", "/admin-panel/", "dashboard"),
    ("Users", "/admin-panel/users/", "users"),
    ("Categories", "/admin-panel/categories/", "categories"),
    ("Grievances", "/admin-panel/grievances/", "grievances"),
    ("Notices", "/admin-panel/notices/", "notices"),
    ("Jobs", "/admin-panel/jobs/", "jobs"),
    # divider
    ("", "", "divider"),
    ("My Profile", "/admin-panel/profile/", "admin_profile"),
]


def _ctx(active, **extra):
    return {"active": active, "sidebar_nav": _NAV, **extra}