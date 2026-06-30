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


def grievances(request):
    return placeholder_page(
        request, "Grievances",
        "The grievance submission and tracking form will live here."
    )


def job_listings(request):
    return render(request, "client/job_listings.html")


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
