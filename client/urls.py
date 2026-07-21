from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("notices/", views.notices, name="notices"),
    path("notices/<int:pk>/", views.notice_detail, name="notice_detail"),
    path("notices/<int:pk>/pdf/", views.notice_pdf, name="notice_pdf"),
    path("notices/<int:pk>/download/", views.notice_download, name="notice_download"),

    path("grievances/", views.grievances, name="grievances"),
    path("grievances/create/", views.grievances, name="grievance_create"),
    path("grievances/track/", views.track_grievance, name="track_grievance"),
    path("grievances/<int:pk>/", views.grievance_detail, name="grievance_detail"),

    path("jobs/", views.job_listings, name="job_listings"),
    path("jobs/<int:pk>/", views.job_detail, name="job_detail"),
    path("jobs/<int:pk>/pdf/", views.job_pdf, name="job_pdf"),
    path("jobs/<int:pk>/download/", views.job_download, name="job_download"),

    path("about/", views.about, name="about"),

    # Auth
    path("login/", views.login_signup, name="login"),
    path("signup/", views.signup_view, name="signup"),
    path("logout/", views.client_logout, name="client_logout"),

    # Profile
    path("profile/", views.profile, name="profile"),
    path("notifications/", views.notifications, name="notifications"),

    # APIs
    path("api/check-username/", views.check_username, name="check_username"),
    path("api/notices/<int:pk>/save/", views.toggle_save_notice, name="toggle_save_notice"),
    path("api/jobs/<int:pk>/save/", views.toggle_save_job, name="toggle_save_job"),
    path("api/notifications/settings/", views.update_notification_setting, name="update_notification_setting"),
]