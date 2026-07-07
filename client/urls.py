from django.urls import path
from . import views


urlpatterns = [
    path("", views.home, name="home"),
    path("notices/", views.notices, name="notices"),

    # ── Notice detail ───────────────────────────────────────
    path("notices/<int:pk>/", views.notice_detail, name="notice_detail"),
    path("notices/<int:pk>/pdf/", views.notice_pdf, name="notice_pdf"),
    path("notices/<int:pk>/download/", views.notice_download, name="notice_download"),

    path("grievances/", views.grievances, name="grievances"),
    path("grievances/create/", views.grievances, name="grievance_create"),

    path("jobs/", views.job_listings, name="job_listings"),

    # ── Job listing detail ──────────────────────────────────
    path("jobs/<int:pk>/", views.job_detail, name="job_detail"),
    path("jobs/<int:pk>/pdf/", views.job_pdf, name="job_pdf"),
    path("jobs/<int:pk>/download/", views.job_download, name="job_download"),

    path("about/", views.about, name="about"),
    path("login/", views.login_view, name="login"),
]