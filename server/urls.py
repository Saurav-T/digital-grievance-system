from django.urls import path
from . import views

app_name = "admin_panel"

urlpatterns = [
    path("", views.dashboard, name="dashboard"),
    path("users/", views.users, name="users"),
    path("grievances/", views.grievances, name="grievances"),
    path("notices/", views.notices, name="notices"),
    path("jobs/", views.jobs, name="jobs"),
]
