from django.shortcuts import render
from django.http import HttpResponse
from django.views.decorators.clickjacking import xframe_options_exempt

from .generators import (
    generate_notice_pdf,
    generate_notice_docx,
    generate_job_pdf,
    generate_job_docx,
)


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


# =============================================================================
# Home
# =============================================================================

def home(request):
    notices = [
        {
            "title": "नवीकरण तथा बेरूजु रकम दाखिला गर्ने सम्बन्धी सूचना",
            "posted_at": "June 18, 2026, 09:33 AM",
        },
        {
            "title": "नवीकरण तथा बेरूजु रकम दाखिला गर्ने सम्बन्धी सूचना",
            "posted_at": "June 18, 2026, 09:33 AM",
        },
        {
            "title": "नवीकरण तथा बेरूजु रकम दाखिला गर्ने सम्बन्धी सूचना",
            "posted_at": "June 18, 2026, 09:33 AM",
        },
        {
            "title": "नवीकरण तथा बेरूजु रकम दाखिला गर्ने सम्बन्धी सूचना",
            "posted_at": "June 18, 2026, 09:33 AM",
        },
    ]

    jobs = [
        {
            "title": "Computer Operator",
            "organization": "Ministry of Education",
            "location": "Kathmandu, Nepal",
            "deadline": "30th July, 2026",
        },
        {
            "title": "Computer Operator",
            "organization": "Ministry of Education",
            "location": "Kathmandu, Nepal",
            "deadline": "30th July, 2026",
        },
        {
            "title": "IT Officer",
            "organization": "Ministry of Home Affairs",
            "location": "Kathmandu, Nepal",
            "deadline": "15th August, 2026",
        },
        {
            "title": "Field Surveyor",
            "organization": "Ministry of Urban Development",
            "location": "Pokhara, Nepal",
            "deadline": "5th August, 2026",
        },
    ]

    stats = {
        "complaints": 100,
        "resolved": 100,
        "active_jobs": 100,
        "notices": 100,
    }

    return render(
        request,
        "client/home.html",
        {
            "notices": notices,
            "jobs": jobs,
            "stats": stats,
        },
    )


# =============================================================================
# Placeholder Pages
# =============================================================================

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
# Notice List
# =============================================================================

def notices(request):
    notices = [
        {"title": "नवीकरण तथा बेरूजु रकम दाखिला गर्ने सम्बन्धी सूचना",
            "posted_at": "June 18, 2026, 09:33 AM"},
        {"title": "अनलाइन उजुरी दर्ता प्रणाली सञ्चालन सम्बन्धी सूचना",
            "posted_at": "June 17, 2026, 02:15 PM"},
        {"title": "कम्प्युटर अपरेटर पदको दरखास्त आह्वान सम्बन्धी सूचना",
            "posted_at": "June 16, 2026, 11:00 AM"},
        {"title": "गुनासो सुनुवाई कार्यक्रम तालिका प्रकाशन सम्बन्धी सूचना",
            "posted_at": "June 15, 2026, 04:45 PM"},
        {"title": "सार्वजनिक बिदाका दिन सेवा उपलब्ध नहुने सम्बन्धी सूचना",
            "posted_at": "June 14, 2026, 10:20 AM"},
        {"title": "वेबसाइट अनुसूची अपडेट सम्बन्धी सूचना",
            "posted_at": "June 13, 2026, 03:30 PM"},
        {"title": "नतिजा प्रकाशन सम्बन्धी जरुरी सूचना",
            "posted_at": "June 12, 2026, 08:00 AM"},
        {"title": "नवीकरण तथा बेरूजु रकम दाखिला गर्ने सम्बन्धी सूचना",
            "posted_at": "June 11, 2026, 01:10 PM"},
        {"title": "अनलाइन उजुरी दर्ता प्रणाली सञ्चालन सम्बन्धी सूचना",
            "posted_at": "June 10, 2026, 09:55 AM"},
    ]

    return render(request, "client/notices.html", {"notices": notices})


# =============================================================================
# Notice Detail
# =============================================================================

def notice_detail(request, pk):
    notice = EXAMPLE_NOTICE.copy()
    notice["id"] = pk

    return render(
        request,
        "client/notice_detail.html",
        {
            "notice": notice,
            "recent_notices": EXAMPLE_RECENT_NOTICES,
        },
    )


@xframe_options_exempt
def notice_pdf(request, pk):
    ctx = {
        "ministry_name": EXAMPLE_NOTICE["ministry_name"],
        "address": EXAMPLE_NOTICE["address"],
        "title": EXAMPLE_NOTICE["doc_title"],
        "date": EXAMPLE_NOTICE["doc_date"],
        "body": EXAMPLE_NOTICE["body"],
    }

    pdf = generate_notice_pdf(ctx)

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'inline; filename="notice_{pk}.pdf"'
    return response


def notice_download(request, pk):
    ctx = {
        "ministry_name": EXAMPLE_NOTICE["ministry_name"],
        "address": EXAMPLE_NOTICE["address"],
        "title": EXAMPLE_NOTICE["doc_title"],
        "date": EXAMPLE_NOTICE["doc_date"],
        "body": EXAMPLE_NOTICE["body"],
    }

    pdf = generate_notice_pdf(ctx)

    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="notice_{pk}.pdf"'
    return response


# =============================================================================
# Grievances
# =============================================================================

def grievances(request):
    return render(request, "client/grievance_form.html")


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
# About / Login
# =============================================================================

def about(request):
    return placeholder_page(
        request,
        "About Us",
        "Background on the Ministry of Home Affairs and this system will live here.",
    )


def login_view(request):
    return placeholder_page(
        request,
        "Login",
        "The login / registration form will live here.",
    )
