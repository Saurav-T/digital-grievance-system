import json
import re
from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.db.models.functions import TruncMonth
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.http import require_POST

from .models import (
    Category,
    Grievance,
    GrievanceStatusHistory,
    JobListing,
    Notice,
    NotificationPreference,
    NoticeView,
    SavedJobListing,
    SavedNotice,
    User,
)

from .generators import (
    generate_notice_pdf,
    generate_notice_docx,
    generate_job_pdf,
    generate_job_docx,
)


# =============================================================================
# Home
# =============================================================================

def home(request):
    notices_qs = Notice.objects.order_by("-issue_date", "-created_at")[:4]
    jobs_qs = JobListing.objects.filter(is_active=True).order_by("-created_at")[:4]

    notices = [
        {"id": n.id, "title": n.title,
         "posted_at": n.issue_date.strftime("%B %d, %Y, %I:%M %p") if n.issue_date else ""}
        for n in notices_qs
    ]
    jobs = [
        {"id": j.id, "title": j.job_title, "organization": j.department,
         "location": j.department_location, "deadline": j.deadline.strftime("%dth %B, %Y")}
        for j in jobs_qs
    ]

    stats = {
        "complaints": Grievance.objects.count(),
        "resolved": Grievance.objects.filter(status="Resolved").count(),
        "active_jobs": JobListing.objects.filter(is_active=True).count(),
        "notices": Notice.objects.count(),
    }

    marquee_notices = [{"text": n["title"], "url": f"/notices/{n['id']}/"} for n in notices]
    marquee_notices += [
        {"text": f"Job Opening: {j['title']} – {j['organization']}", "url": f"/jobs/{j['id']}/"}
        for j in jobs[:2]
    ]

    return render(request, "client/home.html", {
        "notices": notices,
        "jobs": jobs,
        "stats": stats,
        "marquee_notices_json": json.dumps(marquee_notices, ensure_ascii=False),
    })


# =============================================================================
# Auth: Login / Signup / Logout
# =============================================================================

def login_signup(request):
    """
    GET  -> render the combined login/signup page.
    POST -> handle the LOGIN form only (form_type=login).
    The signup form posts to its own endpoint (see signup_view below).
    """
    if request.method == "POST" and request.POST.get("form_type") == "login":
        email = request.POST.get("email", "").strip().lower()
        password = request.POST.get("password", "")
        user = authenticate(request, username=email, password=password)
        if user is not None:
            if not user.is_active:
                messages.error(request, "This account is inactive. Please contact support.")
            else:
                login(request, user)
                return redirect("profile")
        else:
            messages.error(request, "Invalid email or password.")

    return render(request, "client/login.html", {"show_marquee": False})


def signup_view(request):
    """Handles the multi-step signup wizard submission (POST only, single request)."""
    if request.method == "POST":
        full_name    = request.POST.get("full_name", "").strip()
        email        = request.POST.get("email", "").strip().lower()
        username     = request.POST.get("username", "").strip()
        password     = request.POST.get("password", "")
        password2    = request.POST.get("password2", "")
        phone        = request.POST.get("phone_number", "").strip()
        dob          = request.POST.get("dob") or None
        gender       = request.POST.get("gender", "")
        address      = request.POST.get("address", "").strip()
        municipality = request.POST.get("municipality", "").strip()
        avatar       = request.FILES.get("profile_picture")

        errors = []
        if not full_name:
            errors.append("Please enter your full name.")
        if not email or "@" not in email:
            errors.append("Please enter a valid email address.")
        elif User.objects.filter(email__iexact=email).exists():
            errors.append("An account with this email already exists.")

        if not re.match(r"^[a-zA-Z0-9_]{3,20}$", username or ""):
            errors.append("Username must be 3–20 characters (letters, numbers, underscore only).")
        elif User.objects.filter(username__iexact=username).exists():
            errors.append("That username is already taken.")

        if len(password) < 8:
            errors.append("Password must be at least 8 characters.")
        if password != password2:
            errors.append("Passwords do not match.")

        if not phone:
            errors.append("Phone number is required.")
        if not dob:
            errors.append("Date of birth is required.")
        if not address:
            errors.append("Address is required.")
        if not municipality:
            errors.append("Municipality / City is required.")

        if errors:
            for e in errors:
                messages.error(request, e)
            return render(request, "client/login.html", {"show_signup": True})

        name_parts = full_name.split(" ", 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            username=username,
            phone_number=phone,
            dob=dob,
            gender=gender,
            address=address,
            municipality=municipality,
            user_type="Citizen",
        )
        if avatar:
            user.profile_picture = avatar
            user.save()

        NotificationPreference.objects.get_or_create(user=user)

        messages.success(request, "Account created successfully! You can now sign in.")
        return redirect("login")

    return redirect("login")


def check_username(request):
    """GET /api/check-username/?u=value -> {"valid_format": bool, "available": bool}"""
    u = request.GET.get("u", "").strip()
    valid_format = bool(re.match(r"^[a-zA-Z0-9_]{3,20}$", u))
    available = valid_format and not User.objects.filter(username__iexact=u).exists()
    return JsonResponse({"valid_format": valid_format, "available": available})


def client_logout(request):
    logout(request)
    return redirect("login")


# =============================================================================
# Notice List
# =============================================================================

def notices(request):
    notices_qs = Notice.objects.order_by("-issue_date", "-created_at")

    saved_ids = set()
    if request.user.is_authenticated:
        saved_ids = set(
            SavedNotice.objects.filter(user=request.user).values_list("notice_id", flat=True)
        )

    notice_payload = [
        {
            "id": notice.id,
            "title": notice.title,
            "posted_at": notice.issue_date.strftime("%B %d, %Y, %I:%M %p") if notice.issue_date else "",
            "category": notice.category,
            "description": notice.description,
            "is_saved": notice.id in saved_ids,
        }
        for notice in notices_qs
    ]

    return render(request, "client/notices.html", {
        "notices": notice_payload,
        "marquee_notices_json": json.dumps(
            [{"text": n["title"], "url": f"/notices/{n['id']}/"} for n in notice_payload],
            ensure_ascii=False,
        ),
    })


# =============================================================================
# Notice Detail + PDF/Download
# =============================================================================

def notice_detail(request, pk):
    notice = get_object_or_404(Notice, pk=pk)

    # Track the view for the profile "Notice Interest Analysis" / activity chart
    if request.user.is_authenticated:
        NoticeView.objects.create(user=request.user, notice=notice)

    recent_notices = Notice.objects.exclude(pk=notice.pk).order_by("-issue_date", "-created_at")[:5]

    is_saved = (
        request.user.is_authenticated
        and SavedNotice.objects.filter(user=request.user, notice=notice).exists()
    )

    notice_payload = {
        "id": notice.id,
        "title": notice.title,
        "date": notice.issue_date.strftime("%d/%m/%Y") if notice.issue_date else "",
        "ministry_name": "",
        "address": "",
        "doc_title": notice.title,
        "doc_date": notice.issue_date.strftime("%d/%m/%Y") if notice.issue_date else "",
        "body": notice.description,
        "attached_media": [],
        "is_saved": is_saved,
    }

    recent_payload = [
        {
            "id": recent.id,
            "title": recent.title,
            "date": recent.issue_date.strftime("%B %d, %Y, %I:%M %p") if recent.issue_date else "",
        }
        for recent in recent_notices
    ]

    return render(
        request,
        "client/notice_detail.html",
        {
            "notice": notice_payload,
            "recent_notices": recent_payload,
        },
    )


@xframe_options_exempt
def notice_pdf(request, pk):
    notice = get_object_or_404(Notice, pk=pk)
    ctx = {
        "ministry_name": "",
        "address": "",
        "title": notice.title,
        "date": notice.issue_date.strftime("%d/%m/%Y") if notice.issue_date else "",
        "body": notice.description,
    }

    pdf = generate_notice_pdf(ctx)

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="notice_{pk}.pdf"'
    return response


def notice_download(request, pk):
    notice = get_object_or_404(Notice, pk=pk)
    ctx = {
        "ministry_name": "",
        "address": "",
        "title": notice.title,
        "date": notice.issue_date.strftime("%d/%m/%Y") if notice.issue_date else "",
        "body": notice.description,
    }

    docx_bytes = generate_notice_docx(ctx)

    response = HttpResponse(
        docx_bytes,
        content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    response["Content-Disposition"] = f'attachment; filename="notice_{pk}.docx"'
    return response


# =============================================================================
# Save / Unsave toggles (AJAX)
# =============================================================================

def toggle_save_notice(request, pk):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "auth_required"}, status=401)
    notice = get_object_or_404(Notice, pk=pk)
    obj, created = SavedNotice.objects.get_or_create(user=request.user, notice=notice)
    if not created:
        obj.delete()
        return JsonResponse({"saved": False})
    return JsonResponse({"saved": True})


def toggle_save_job(request, pk):
    if not request.user.is_authenticated:
        return JsonResponse({"error": "auth_required"}, status=401)
    job = get_object_or_404(JobListing, pk=pk)
    obj, created = SavedJobListing.objects.get_or_create(user=request.user, job=job)
    if not created:
        obj.delete()
        return JsonResponse({"saved": False})
    return JsonResponse({"saved": True})


@login_required(login_url="login")
@require_POST
def update_notification_setting(request):
    key = request.POST.get("key")
    enabled = request.POST.get("enabled") == "true"
    mapping = {
        "new_notice": "new_notices",
        "grievance_update": "grievance_updates",
        "new_job": "new_job_listings",
    }
    field = mapping.get(key)
    if not field:
        return JsonResponse({"error": "invalid key"}, status=400)

    pref, _ = NotificationPreference.objects.get_or_create(user=request.user)
    setattr(pref, field, enabled)
    pref.save()
    return JsonResponse({"success": True})


# =============================================================================
# Grievances (create + track, DB-backed)
# =============================================================================

@login_required(login_url="login")
def grievances(request):
    """
    GET  -> render the grievance submission form.
    POST -> create a new Grievance for the logged-in user.
    """
    if request.method == "POST":
        subject = request.POST.get("subject", "").strip()
        description = request.POST.get("description", "").strip()
        priority_raw = request.POST.get("priority", "medium").capitalize()
        category_raw = request.POST.get("category", "other").replace("_", " ").title()
        coordinates = request.POST.get("coordinates", "").strip()

        if not subject or not description:
            messages.error(request, "Please provide both a subject and a description.")
            return redirect("grievance_create")

        valid_priorities = dict(Grievance.PRIORITY_CHOICES)
        priority = priority_raw if priority_raw in valid_priorities else "Medium"

        category, _ = Category.objects.get_or_create(name=category_raw)

        grievance = Grievance.objects.create(
            user=request.user,
            category=category,
            subject=subject,
            description=description,
            priority=priority,
            location_url=coordinates or None,
        )

        files = request.FILES.getlist("attachments")
        if files:
            grievance.attachment = files[0]
            grievance.save()

        GrievanceStatusHistory.objects.create(
            grievance=grievance,
            status="Pending",
            remarks="Submitted by citizen.",
            updated_by=request.user,
        )

        messages.success(request, "Your grievance has been submitted successfully.")
        return redirect("track_grievance")

    return render(request, "client/grievance_form.html")


@login_required(login_url="login")
def track_grievance(request):
    qs = (
        Grievance.objects.filter(user=request.user)
        .select_related("category")
        .order_by("-created_at")
    )

    q = request.GET.get("q", "").strip()
    status_filter = request.GET.get("filter", "")

    if q:
        qs = qs.filter(Q(subject__icontains=q) | Q(category__name__icontains=q))

    if status_filter:
        status_map = {
            "pending": "Pending",
            "in_progress": "In Review",
            "resolved": "Resolved",
            "rejected": "Rejected",
        }
        qs = qs.filter(status=status_map.get(status_filter, status_filter))

    return render(request, "client/track_grievance.html", {"grievances": qs})


@login_required(login_url="login")
def grievance_detail(request, pk):
    grievance = get_object_or_404(
        Grievance.objects.select_related("user", "category"),
        pk=pk,
        user=request.user,
    )
    history = grievance.status_history.select_related("updated_by").order_by("updated_at")
    return render(
        request,
        "client/grievance_detail.html",
        {"grievance": grievance, "history": history},
    )


# =============================================================================
# Job Listings (DB-backed)
# =============================================================================

def job_listings(request):
    jobs_qs = JobListing.objects.filter(is_active=True).order_by("-created_at")

    saved_ids = set()
    if request.user.is_authenticated:
        saved_ids = set(
            SavedJobListing.objects.filter(user=request.user).values_list("job_id", flat=True)
        )

    job_payload = [
        {
            "id": j.id,
            "title": j.job_title,
            "org": j.department,
            "location": j.department_location,
            "deadline": j.deadline.isoformat(),
            "url": f"/jobs/{j.id}/",
            "is_saved": j.id in saved_ids,
        }
        for j in jobs_qs
    ]

    return render(request, "client/job_listings.html", {
        "jobs_json": json.dumps(job_payload, ensure_ascii=False),
    })


def job_detail(request, pk):
    job = get_object_or_404(JobListing, pk=pk)
    recent_jobs = (
        JobListing.objects.exclude(pk=pk).filter(is_active=True).order_by("-created_at")[:5]
    )

    is_saved = (
        request.user.is_authenticated
        and SavedJobListing.objects.filter(user=request.user, job=job).exists()
    )

    job_payload = {
        "id": job.id,
        "title": job.job_title,
        "date": job.issue_date.strftime("%d/%m/%Y") if job.issue_date else "",
        "department": job.department,
        "location": job.department_location,
        "doc_title": job.job_title,
        "doc_date": job.issue_date.strftime("%d/%m/%Y") if job.issue_date else "",
        "description": job.job_description,
        "requirements": job.job_requirements,
        "age_requirement": job.age_requirement,
        "deadline": job.deadline.strftime("%d %B, %Y") if job.deadline else "",
        "contact": job.contact_information,
        "contact_email": "",
        "attached_media": [],
        "is_saved": is_saved,
    }

    recent_payload = [
        {
            "id": r.id,
            "title": r.job_title,
            "department": r.department,
            "location": r.department_location,
            "deadline": r.deadline.strftime("%d %b %Y") if r.deadline else "",
        }
        for r in recent_jobs
    ]

    return render(
        request,
        "client/job_detail.html",
        {"job": job_payload, "recent_jobs": recent_payload},
    )


@xframe_options_exempt
def job_pdf(request, pk):
    job = get_object_or_404(JobListing, pk=pk)
    ctx = {
        "department": job.department,
        "location": job.department_location,
        "title": job.job_title,
        "date": job.issue_date.strftime("%d/%m/%Y") if job.issue_date else "",
        "description": job.job_description,
        "requirements": job.job_requirements,
        "age_requirement": job.age_requirement,
        "deadline": job.deadline.strftime("%d %B, %Y") if job.deadline else "",
        "contact": job.contact_information,
    }

    pdf = generate_job_pdf(ctx)

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="job_{pk}.pdf"'
    return response


def job_download(request, pk):
    job = get_object_or_404(JobListing, pk=pk)
    ctx = {
        "department": job.department,
        "location": job.department_location,
        "title": job.job_title,
        "date": job.issue_date.strftime("%d/%m/%Y") if job.issue_date else "",
        "description": job.job_description,
        "requirements": job.job_requirements,
        "age_requirement": job.age_requirement,
        "deadline": job.deadline.strftime("%d %B, %Y") if job.deadline else "",
        "contact": job.contact_information,
    }

    pdf = generate_job_pdf(ctx)

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="job_{pk}.pdf"'
    return response


# =============================================================================
# About
# =============================================================================

def about(request):
    return render(request, 'client/about.html', {
        'citizen_features': [
            'Secure Registration', 'Online Complaint Submission',
            'Complaint Status Tracking', 'Notice Board', 'User Profile', 'Notifications',
        ],
        'admin_features': [
            'Notice Management', 'Grievance Management', 'User Management',
            'Dashboard Analytics', 'Role-Based Access', 'Report Generation',
        ],
    })


def placeholder_page(request, page_title, page_description=""):
    return render(
        request,
        "placeholder.html",
        {
            "page_title": page_title,
            "page_description": page_description,
        },
    )


# =============================================================================
# Profile view (fully DB-backed)
# =============================================================================

@login_required(login_url="login")
def profile(request):
    user = request.user
    now = timezone.now()

    # ── Core grievance stats ─────────────────────────────────────────────
    grievances_qs = Grievance.objects.filter(user=user)
    total_grievances = grievances_qs.count()
    this_month_count = grievances_qs.filter(
        created_at__year=now.year, created_at__month=now.month
    ).count()
    resolved_qs = grievances_qs.filter(status="Resolved")
    resolved_count = resolved_qs.count()
    pending_count = grievances_qs.exclude(status__in=["Resolved", "Rejected"]).count()

    # ── Saved items ───────────────────────────────────────────────────────
    saved_notices_qs = (
        SavedNotice.objects.filter(user=user).select_related("notice").order_by("-saved_at")
    )
    saved_jobs_qs = (
        SavedJobListing.objects.filter(user=user).select_related("job").order_by("-saved_at")
    )

    # ── Monthly activity: last 12 months ─────────────────────────────────
    since = now - timedelta(days=365)
    griev_monthly = (
        grievances_qs.filter(created_at__gte=since)
        .annotate(month=TruncMonth("created_at"))
        .values("month")
        .annotate(count=Count("id"))
    )
    notice_monthly = (
        NoticeView.objects.filter(user=user, viewed_at__gte=since)
        .annotate(month=TruncMonth("viewed_at"))
        .values("month")
        .annotate(count=Count("id"))
    )
    griev_map = {g["month"].strftime("%Y-%m"): g["count"] for g in griev_monthly}
    notice_map = {n["month"].strftime("%Y-%m"): n["count"] for n in notice_monthly}

    labels, griev_series, notice_series = [], [], []
    y, m = now.year, now.month
    months = []
    for i in range(11, -1, -1):
        mm, yy = m - i, y
        while mm <= 0:
            mm += 12
            yy -= 1
        months.append((yy, mm))
    for yy, mm in months:
        key = f"{yy:04d}-{mm:02d}"
        labels.append(timezone.datetime(yy, mm, 1).strftime("%b"))
        griev_series.append(griev_map.get(key, 0))
        notice_series.append(notice_map.get(key, 0))

    # ── Category analytics (top 3) ───────────────────────────────────────
    cat_qs = (
        grievances_qs.exclude(category__isnull=True)
        .values("category__name")
        .annotate(count=Count("id"))
        .order_by("-count")[:3]
    )
    category_analytics = []
    if total_grievances:
        for c in cat_qs:
            category_analytics.append({
                "label": c["category__name"],
                "pct": round((c["count"] / total_grievances) * 100),
            })

    # ── Resolution analytics ──────────────────────────────────────────────
    resolved_with_time = resolved_qs.exclude(resolved_at__isnull=True)
    durations = [
        (g.resolved_at - g.created_at).total_seconds() / 86400 for g in resolved_with_time
    ]
    avg_days = round(sum(durations) / len(durations), 1) if durations else 0
    fastest_days = round(min(durations), 1) if durations else 0
    longest_days = round(max(durations), 1) if durations else 0

    # ── Notice interest analysis (top 5 viewed categories) ────────────────
    total_views = NoticeView.objects.filter(user=user).count()
    interest_qs = (
        NoticeView.objects.filter(user=user)
        .values("notice__category")
        .annotate(count=Count("id"))
        .order_by("-count")[:5]
    )
    notice_interests = []
    if total_views:
        category_labels = dict(Notice.CATEGORY_CHOICES)
        for i in interest_qs:
            notice_interests.append({
                "label": category_labels.get(i["notice__category"], "General"),
                "pct": round((i["count"] / total_views) * 100),
            })

    # ── Trend analytics: this month vs last month ─────────────────────────
    last_month_ref = now.replace(day=1) - timedelta(days=1)
    notices_this_month = NoticeView.objects.filter(
        user=user, viewed_at__year=now.year, viewed_at__month=now.month
    ).count()
    notices_last_month = NoticeView.objects.filter(
        user=user, viewed_at__year=last_month_ref.year, viewed_at__month=last_month_ref.month
    ).count()
    griev_last_month = grievances_qs.filter(
        created_at__year=last_month_ref.year, created_at__month=last_month_ref.month
    ).count()
    resolved_this_month = resolved_qs.filter(
        resolved_at__year=now.year, resolved_at__month=now.month
    ).count()
    resolved_last_month = resolved_qs.filter(
        resolved_at__year=last_month_ref.year, resolved_at__month=last_month_ref.month
    ).count()

    def pct_change(cur, prev):
        if prev == 0:
            return 100 if cur > 0 else 0
        return round(((cur - prev) / prev) * 100)

    rate_this_month = round((resolved_this_month / this_month_count) * 100) if this_month_count else 0
    rate_last_month = round((resolved_last_month / griev_last_month) * 100) if griev_last_month else 0

    trends = [
        {
            "label": "Notices Viewed",
            "value": f"{pct_change(notices_this_month, notices_last_month):+d}%",
            "positive": notices_this_month >= notices_last_month,
        },
        {
            "label": "Grievances Submitted",
            "value": f"{pct_change(this_month_count, griev_last_month):+d}%",
            "positive": this_month_count >= griev_last_month,
        },
        {
            "label": "Resolution Rate",
            "value": f"{pct_change(rate_this_month, rate_last_month):+d}%",
            "positive": rate_this_month >= rate_last_month,
        },
    ]

    # ── Insights (derived from the numbers above) ─────────────────────────
    insights = []
    if category_analytics:
        insights.append({
            "icon": "🛣️",
            "text": f"{category_analytics[0]['label']} issues are your most common reports.",
        })
    if total_grievances:
        insights.append({
            "icon": "✅",
            "text": f"{round((resolved_count / total_grievances) * 100)}% of your grievances were resolved.",
        })
    if durations:
        insights.append({"icon": "⏱️", "text": f"Your average response time is {avg_days} days."})
    if notice_interests:
        insights.append({
            "icon": "👀",
            "text": f"You view {notice_interests[0]['label']} notices the most.",
        })
    if not insights:
        insights.append({
            "icon": "📋",
            "text": "Submit a grievance or browse notices to start seeing insights here.",
        })

    # ── Notification preferences ──────────────────────────────────────────
    pref, _ = NotificationPreference.objects.get_or_create(user=user)
    notification_settings = [
        {
            "key": "new_notice", "label": "New Notices",
            "desc": "Notify when a new notice is published.", "enabled": pref.new_notices,
        },
        {
            "key": "grievance_update", "label": "Grievance Updates",
            "desc": "Notify when your grievance status changes.", "enabled": pref.grievance_updates,
        },
        {
            "key": "new_job", "label": "New Job Listings",
            "desc": "Notify when a new job listing is added.", "enabled": pref.new_job_listings,
        },
    ]

    # ── Profile display data ──────────────────────────────────────────────
    profile_dict = {
        "name": user.get_full_name() or "User",
        "email": user.email,
        "location": user.municipality or "—",
        "phone": user.phone_number or "—",
        "address": user.address or "—",
        "dob": user.dob.strftime("%d %b %Y") if user.dob else "—",
        "gender": user.gender or "—",
        "joined": user.date_joined.strftime("%B %Y"),
        "avatar_url": user.avatar_url,
    }

    personal_fields = [
        {"label": "Full Name", "value": profile_dict["name"]},
        {"label": "Email", "value": profile_dict["email"]},
        {"label": "Phone", "value": profile_dict["phone"]},
        {"label": "Date of Birth", "value": profile_dict["dob"]},
        {"label": "Gender", "value": profile_dict["gender"]},
        {"label": "Address", "value": profile_dict["address"]},
        {"label": "Municipality", "value": profile_dict["location"]},
        {"label": "Member Since", "value": profile_dict["joined"]},
    ]

    saved_notices = [
        {
            "id": sn.notice.id,
            "title": sn.notice.title,
            "date": sn.notice.issue_date.strftime("%B %d, %Y") if sn.notice.issue_date else "",
        }
        for sn in saved_notices_qs
    ]
    saved_jobs = [
        {
            "id": sj.job.id,
            "title": sj.job.job_title,
            "department": sj.job.department,
            "deadline": sj.job.deadline.strftime("%d %b %Y") if sj.job.deadline else "",
        }
        for sj in saved_jobs_qs
    ]

    return render(request, "client/profile.html", {
        "profile": profile_dict,
        "personal_fields": personal_fields,
        "insights": insights,
        "notice_interests": notice_interests,
        "trends": trends,
        "saved_notices": saved_notices,
        "saved_jobs": saved_jobs,
        "notification_settings": notification_settings,

        "grievances_total": total_grievances,
        "grievances_this_month": this_month_count,
        "resolved_count": resolved_count,
        "pending_count": pending_count,
        "saved_notices_count": len(saved_notices),

        "activity_labels_json": json.dumps(labels),
        "activity_notices_json": json.dumps(notice_series),
        "activity_grievances_json": json.dumps(griev_series),

        "category_analytics": category_analytics,
        "avg_resolution_days": avg_days,
        "fastest_resolution_days": fastest_days,
        "longest_resolution_days": longest_days,
    })


def notifications(request):
    return render(request, "client/notifications.html")