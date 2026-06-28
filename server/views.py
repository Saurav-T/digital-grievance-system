from django.shortcuts import render


def dashboard(request):
    stats = {
        "total_complaints": 100,
        "complaints_this_month": 17,
        "total_notices": 100,
        "active_users": 100,
        "job_listings": 100,
    }

    recent_grievances = [
        {"id": 1, "date": "21st June, 2026", "subject": "Road Blockage", "category": "Infrastructure", "priority": "Medium", "status": "Pending"},
        {"id": 2, "date": "21st June, 2026", "subject": "Road Blockage", "category": "Infrastructure", "priority": "Medium", "status": "Resolved"},
        {"id": 3, "date": "21st June, 2026", "subject": "Road Blockage", "category": "Infrastructure", "priority": "Medium", "status": "Rejected"},
    ]

    latest_notices = [
        {"id": 1, "date": "21st June, 2026", "title": "Road Blockage", "category": "Infrastructure"},
    ]

    context = {
        "active": "dashboard",
        "stats": stats,
        "recent_grievances": recent_grievances,
        "latest_notices": latest_notices,
    }
    return render(request, "server/dashboard.html", context)


def _placeholder(request, active, page_title, page_description=""):
    return render(request, "server/placeholder.html", {
        "active": active,
        "page_title": page_title,
        "page_description": page_description,
    })


def users(request):
    return _placeholder(request, "users", "Users", "User management table — list, roles, and account actions go here.")


def grievances(request):
    return _placeholder(request, "grievances", "Grievances", "Full grievance management table with filters and status updates goes here.")


def notices(request):
    return _placeholder(request, "notices", "Notices", "Notice management table with create/edit/publish actions goes here.")


def jobs(request):
    return _placeholder(request, "jobs", "Jobs", "Job listing management table with create/edit/close actions goes here.")
