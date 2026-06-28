from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("notices/", views.notices, name="notices"),
    path("grievances/", views.grievances, name="grievances"),
    path("jobs/", views.job_listings, name="job_listings"),
    path("about/", views.about, name="about"),
    path("login/", views.login_view, name="login"),
]
