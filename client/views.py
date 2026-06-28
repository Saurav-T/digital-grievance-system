from django.shortcuts import render


def home(request):
    """
    Landing page view.
    Replace the hard-coded context below with real querysets
    (e.g. Notice.objects.latest(...), Job.objects.filter(...))
    once your models are wired up.
    """
    notices = [
        {"title": "नवीकरण तथा बेरूजु रकम दाखिला गर्ने सम्बन्धी सूचना",
            "posted_at": "June 18, 2026, 09:33 AM"},
        {"title": "नवीकरण तथा बेरूजु रकम दाखिला गर्ने सम्बन्धी सूचना",
            "posted_at": "June 18, 2026, 09:33 AM"},
        {"title": "नवीकरण तथा बेरूजु रकम दाखिला गर्ने सम्बन्धी सूचना",
            "posted_at": "June 18, 2026, 09:33 AM"},
        {"title": "नवीकरण तथा बेरूजु रकम दाखिला गर्ने सम्बन्धी सूचना",
            "posted_at": "June 18, 2026, 09:33 AM"},
    ]

    jobs = [
        {"title": "Computer Operator", "organization": "Ministry of Education",
            "location": "Kathmandu, Nepal", "deadline": "30th July, 2026"},
        {"title": "Computer Operator", "organization": "Ministry of Education",
            "location": "Kathmandu, Nepal", "deadline": "30th July, 2026"},
        {"title": "IT Officer", "organization": "Ministry of Home Affairs",
            "location": "Kathmandu, Nepal", "deadline": "15th August, 2026"},
        {"title": "Field Surveyor", "organization": "Ministry of Urban Development",
            "location": "Pokhara, Nepal", "deadline": "5th August, 2026"},
    ]

    stats = {
        "complaints": 100,
        "resolved": 100,
        "active_jobs": 100,
        "notices": 100,
    }

    context = {
        "notices": notices,
        "jobs": jobs,
        "stats": stats,
    }
    return render(request, "client/home.html", context)


def placeholder_page(request, page_title, page_description=""):
    """Generic placeholder used for sidebar pages that don't have real content yet."""
    return render(request, "placeholder.html", {
        "page_title": page_title,
        "page_description": page_description,
    })


def notices(request):
    return placeholder_page(
        request, "Notices",
        "The full notice board — with search, filters, and pagination — will live here."
    )


def grievances(request):
    return placeholder_page(
        request, "Grievances",
        "The grievance submission and tracking form will live here."
    )


def job_listings(request):
    return placeholder_page(
        request, "Job Listings",
        "The complete, filterable job board will live here."
    )


def about(request):
    return placeholder_page(
        request, "About Us",
        "Background on the Ministry of Home Affairs and this system will live here."
    )


def login_view(request):
    return placeholder_page(
        request, "Login",
        "The login / registration form will live here."
    )
