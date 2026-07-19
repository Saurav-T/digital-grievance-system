import json

from django.shortcuts import get_object_or_404, render
from django.http import HttpResponse
from django.views.decorators.clickjacking import xframe_options_exempt
from django.utils import timezone

from .models import Notice


from .generators import (
    generate_notice_pdf,
    generate_notice_docx,
    generate_job_pdf,
    generate_job_docx,
)

# Preference categories passed to the signup form
SIGNUP_PREF_CATEGORIES = [
    {"value": "govt",   "icon": "🏛️",  "label": "Government Notices", "desc": "Official ministry updates"},
    {"value": "job",    "icon": "💼",  "label": "Job Opportunities",  "desc": "Vacancies & recruitments"},
    {"value": "scholar","icon": "🎓",  "label": "Scholarships",       "desc": "Funding & fellowships"},
    {"value": "events", "icon": "📅",  "label": "Events",             "desc": "Public events & programs"},
    {"value": "public", "icon": "📢",  "label": "Public Announcements","desc": "General public notices"},
    {"value": "infra",  "icon": "🏗️",  "label": "Infrastructure",    "desc": "Construction & development"},
]

# =============================================================================
# Example Data (Replace with database queries later)
# =============================================================================

EXAMPLE_NOTICE = {
    "id": 1,
    "title": (
        "यस मन्त्रालयको मिति 2083-03-19 गतेको निर्णयानुसार "
        "पदस्थापन/सरुवा हुनुभएका रा.प.द्वितीय श्रेणीका कर्मचारीहरूको विवरण"
    ),
    "date": "05/07/2026",
    "ministry_name": "Ministry of Home Affairs",
    "address": "Singhadurbar,\nKathmandu, Nepal",
    "doc_title": "Temporary Closure of Government Offices on Public Holiday",
    "doc_date": "05/08/2026",
    "body": (
        "This is to inform all citizens that government offices under Kathmandu "
        "Metropolitan City will remain closed on Tuesday, 7 July 2026, in observance "
        "of a declared public holiday.\n\n"
        "Essential services will continue to operate as usual."
    ),
    "attached_media": [
        {"name": "official_letter.pdf", "type": "pdf", "size": "245 KB", "url": "#"},
        {"name": "employee_list.docx", "type": "docx", "size": "128 KB", "url": "#"},
        {"name": "notice_header.jpg", "type": "image", "size": "1.2 MB", "url": "#"},
    ],
}

EXAMPLE_RECENT_NOTICES = [
    {
        "id": i,
        "title": "नवीकरण तथा बेरूजु रकम दाखिला गर्ने सम्बन्धी सूचना",
        "date": "June 18, 2026, 09:33 AM",
    }
    for i in range(1, 6)
]

EXAMPLE_JOB = {
    "id": 1,
    "title": (
        "यस मन्त्रालयको मिति 2083-03-19 गतेको निर्णयानुसार "
        "पदस्थापन/सरुवा हुनुभएका रा.प.द्वितीय श्रेणीका कर्मचारीहरूको विवरण"
    ),
    "date": "05/07/2026",
    "department": "Ministry of Education",
    "location": "Kathmandu, Nepal",
    "doc_title": "Computer Operator – Vacancy Announcement",
    "doc_date": "05/07/2026",
    "description": (
        "Applications are invited from Nepali citizens for the following position."
    ),
    "requirements": (
        "SLC/SEE passed or equivalent; basic computer literacy required."
    ),
    "age_requirement": "18–35 years",
    "deadline": "30th July, 2026",
    "contact": (
        "Ministry of Education\n"
        "Keshar Mahal\n"
        "Kathmandu\n"
        "Tel: 01-4200xxx"
    ),
    "attached_media": [
        {"name": "job_vacancy.pdf", "type": "pdf", "size": "312 KB", "url": "#"},
        {"name": "application_form.docx", "type": "docx", "size": "85 KB", "url": "#"},
    ],
}

EXAMPLE_RECENT_JOBS = [
    {
        "id": i,
        "title": "Computer Operator",
        "department": "Ministry of Education",
        "location": "Kathmandu, Nepal",
        "deadline": "30th July, 2026",
    }
    for i in range(1, 6)
]

def login_signup(request):
    """
    Combined login / signup page (client-side switching via JS).
    POST /login/ → handles login (TODO: wire Django auth).
    POST /signup/ → handled by separate endpoint.
    TODO (DB): Use Django's authenticate() / login() for login form.
    """
    if request.method == "POST":
        # TODO: authenticate(request, username=..., password=...)
        pass
    return render(request, "client/login.html", {
        "pref_categories": SIGNUP_PREF_CATEGORIES,
        "show_marquee": False,
    })

# =============================================================================
# Home
# =============================================================================

def home(request):
    notices = [
        {"id": 1, "title": "नवीकरण तथा बेरूजु रकम दाखिला गर्ने सम्बन्धी सूचना",
         "posted_at": "June 18, 2026, 09:33 AM"},
        {"id": 2, "title": "नवीकरण तथा बेरूजु रकम दाखिला गर्ने सम्बन्धी सूचना",
         "posted_at": "June 18, 2026, 09:33 AM"},
        {"id": 3, "title": "नवीकरण तथा बेरूजु रकम दाखिला गर्ने सम्बन्धी सूचना",
         "posted_at": "June 18, 2026, 09:33 AM"},
        {"id": 4, "title": "नवीकरण तथा बेरूजु रकम दाखिला गर्ने सम्बन्धी सूचना",
         "posted_at": "June 18, 2026, 09:33 AM"},
    ]
    jobs = [
        {"id": 1, "title": "Computer Operator",
         "organization": "Ministry of Education",
         "location": "Kathmandu, Nepal",
         "deadline": "30th July, 2026"},
        {"id": 2, "title": "Computer Operator",
         "organization": "Ministry of Education",
         "location": "Kathmandu, Nepal",
         "deadline": "30th July, 2026"},
        {"id": 3, "title": "IT Officer",
         "organization": "Ministry of Home Affairs",
         "location": "Kathmandu, Nepal",
         "deadline": "15th August, 2026"},
        {"id": 4, "title": "Field Surveyor",
         "organization": "Ministry of Urban Development",
         "location": "Pokhara, Nepal",
         "deadline": "5th August, 2026"},
    ]
    stats = {
        "complaints": 100,
        "resolved": 82,
        "active_jobs": 14,
        "notices": 100,
    }

    # Marquee: latest notices as clickable {text, url} objects
    marquee_notices = [
        {"text": n["title"], "url": f"/notices/{n['id']}/"}
        for n in notices
    ]
    # Pad with a couple of job notices
    marquee_notices += [
        {"text": f"Job Opening: {j['title']} – {j['organization']}",
         "url": f"/jobs/{j['id']}/"}
        for j in jobs[:2]
    ]

    return render(request, "client/home.html", {
        "notices": notices,
        "jobs": jobs,
        "stats": stats,
        "marquee_notices_json": json.dumps(marquee_notices, ensure_ascii=False),
    })


# =============================================================================
# Notice List
# =============================================================================

def notices(request):
    notices_qs = Notice.objects.order_by("-issue_date", "-created_at")
    notice_payload = [
        {
            "id": notice.id,
            "title": notice.title,
            "posted_at": notice.issue_date.strftime("%B %d, %Y, %I:%M %p") if notice.issue_date else "",
            "category": "general",
            "description": notice.description,
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
    recent_notices = Notice.objects.exclude(pk=notice.pk).order_by("-issue_date", "-created_at")[:5]

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

    response = HttpResponse(docx_bytes, content_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    response["Content-Disposition"] = f'attachment; filename="notice_{pk}.docx"'
    return response


# =============================================================================
# Grievances
# =============================================================================

def grievances(request):
    return render(request, "client/grievance_form.html")

def track_grievance(request):
    return render(request, "client/track_grievance.html")


# =============================================================================
# Job Listings
# =============================================================================
def job_listings(request):
    return render(request, "client/job_listings.html")


def job_detail(request, pk):
    job = EXAMPLE_JOB.copy()
    job["id"] = pk

    return render(
        request,
        "client/job_detail.html",
        {
            "job": job,
            "recent_jobs": EXAMPLE_RECENT_JOBS,
        },
    )


@xframe_options_exempt
def job_pdf(request, pk):
    ctx = {
        "department": EXAMPLE_JOB["department"],
        "location": EXAMPLE_JOB["location"],
        "title": EXAMPLE_JOB["doc_title"],
        "date": EXAMPLE_JOB["doc_date"],
        "description": EXAMPLE_JOB["description"],
        "requirements": EXAMPLE_JOB["requirements"],
        "age_requirement": EXAMPLE_JOB["age_requirement"],
        "deadline": EXAMPLE_JOB["deadline"],
        "contact": EXAMPLE_JOB["contact"],
    }

    pdf = generate_job_pdf(ctx)

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="job_{pk}.pdf"'
    return response


def job_download(request, pk):
    ctx = {
        "department": EXAMPLE_JOB["department"],
        "location": EXAMPLE_JOB["location"],
        "title": EXAMPLE_JOB["doc_title"],
        "date": EXAMPLE_JOB["doc_date"],
        "description": EXAMPLE_JOB["description"],
        "requirements": EXAMPLE_JOB["requirements"],
        "age_requirement": EXAMPLE_JOB["age_requirement"],
        "deadline": EXAMPLE_JOB["deadline"],
        "contact": EXAMPLE_JOB["contact"],
    }

    pdf = generate_job_pdf(ctx)

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="job_{pk}.pdf"'
    return response


# =============================================================================
# About / Login / Profile
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


def login_view(request):
    return placeholder_page(
        request,
        "Login",
        "The login / registration form will live here.",
    )


def placeholder_page(request, page_title, page_description=""):
    return render(
        request,
        "placeholder.html",
        {
            "page_title": page_title,
            "page_description": page_description,
        },
    )


# ─────────────────────────────────────────────────────────────────────────────
# Profile view
# ─────────────────────────────────────────────────────────────────────────────

def profile(request):
    """
    User profile page.
    TODO (DB): Replace demo data with real queries once User model is linked.
    """
    demo_profile = {
        "name":     "User Name",
        "email":    "username@gmail.com",
        "location": "Kathmandu, Nepal",
        "phone":    "+977 9876543210",
        "address":  "Ward No. 5, Thamel",
        "dob":      "15 Jan 1995",
        "gender":   "Male",
        "joined":   "June 2026",
    }

    personal_fields = [
        {"label": "Full Name",     "value": demo_profile["name"]},
        {"label": "Email",         "value": demo_profile["email"]},
        {"label": "Phone",         "value": demo_profile["phone"]},
        {"label": "Date of Birth", "value": demo_profile["dob"]},
        {"label": "Gender",        "value": demo_profile["gender"]},
        {"label": "Address",       "value": demo_profile["address"]},
        {"label": "Municipality",  "value": "Kathmandu Metropolitan City"},
        {"label": "Member Since",  "value": demo_profile["joined"]},
    ]

    insights = [
        {"icon": "📅", "text": "You submit most grievances on Mondays."},
        {"icon": "🛣️", "text": "Road-related issues are your most common reports."},
        {"icon": "✅", "text": "82% of your grievances were resolved."},
        {"icon": "⏱️", "text": "Your average response time is 4.3 days."},
        {"icon": "👀", "text": "You viewed 3× more job notices than scholarship notices."},
    ]

    notice_interests = [
        {"label": "Jobs",        "pct": 45},
        {"label": "Government",  "pct": 25},
        {"label": "Scholarships","pct": 20},
        {"label": "Events",      "pct": 10},
    ]

    trends = [
        {"label": "Notices Viewed",        "value": "+21%", "positive": True},
        {"label": "Grievances Submitted",  "value": "-15%", "positive": False},
        {"label": "Resolution Rate",       "value": "+12%", "positive": True},
    ]

    saved_notices = [
        {"id": 1, "title": "नवीकरण तथा बेरूजु रकम दाखिला गर्ने सम्बन्धी सूचना",
         "date": "June 18, 2026"},
        {"id": 2, "title": "Public Holiday – 7 July 2026",
         "date": "July 1, 2026"},
    ]
    saved_jobs = [
        {"id": 1, "title": "Computer Operator",
         "department": "Ministry of Education", "deadline": "30 July 2026"},
        {"id": 2, "title": "Data Entry Operator",
         "department": "Ministry of Home Affairs", "deadline": "15 Aug 2026"},
    ]

    notification_settings = [
        {"key": "new_notice",      "label": "New Notices",          "desc": "Notify when a new notice is published.",          "enabled": True},
        {"key": "grievance_update","label": "Grievance Updates",    "desc": "Notify when your grievance status changes.",      "enabled": True},
        {"key": "new_job",         "label": "New Job Listings",     "desc": "Notify when a new job listing is added.",         "enabled": True},
        {"key": "email_digest",    "label": "Weekly Email Digest",  "desc": "Receive a weekly summary to your email.",         "enabled": False},
        {"key": "sms_alerts",      "label": "SMS Alerts",           "desc": "Receive critical updates via SMS.",               "enabled": False},
    ]

    preference_categories = [
        {"value": "govt",   "label": "Government Notices",  "selected": True},
        {"value": "job",    "label": "Job Opportunities",   "selected": True},
        {"value": "scholar","label": "Scholarships",        "selected": False},
        {"value": "events", "label": "Events",              "selected": False},
        {"value": "public", "label": "Public Announcements","selected": True},
        {"value": "infra",  "label": "Infrastructure",      "selected": False},
    ]

    return render(request, "client/profile.html", {
        "profile":                demo_profile,
        "personal_fields":        personal_fields,
        "insights":               insights,
        "notice_interests":       notice_interests,
        "trends":                 trends,
        "saved_notices":          saved_notices,
        "saved_jobs":             saved_jobs,
        "notification_settings":  notification_settings,
        "preference_categories":  preference_categories,
    })

def notifications(request):
    return render(request, "client/notifications.html")