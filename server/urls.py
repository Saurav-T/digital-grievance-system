from django.urls import path
from . import views

app_name = "admin_panel"

urlpatterns = [
    # Auth
    path("login/",  views.admin_login,  name="login"),
    path("logout/", views.admin_logout, name="logout"),

    # Dashboard
    path("", views.dashboard, name="dashboard"),

    # Users
    path("users/", views.users, name="users"),
    path("users/<int:pk>/json/", views.user_json, name="user_json"),

    # Categories
    path("categories/", views.categories, name="categories"),
    path("categories/<int:pk>/json/", views.category_json, name="category_json"),

    # Grievances
    path("grievances/", views.grievances, name="grievances"),
    path("grievances/<int:pk>/json/",
         views.grievance_json,  name="grievance_json"),
    path("grievances/<int:pk>/pdf/",  views.grievance_pdf,   name="grievance_pdf"),

    # Notices
    path("notices/", views.notices, name="notices"),
    path("notices/<int:pk>/json/", views.notice_json, name="notice_json"),

    # Jobs
    path("jobs/", views.jobs, name="jobs"),
    path("jobs/<int:pk>/json/", views.job_json, name="job_json"),

     path('carousel/upload/',          views.carousel_upload,  name='carousel_upload'),
    path('carousel/<int:pk>/delete/', views.carousel_delete,  name='carousel_delete'),
    path('carousel/reorder/',         views.carousel_reorder, name='carousel_reorder'),
    path('carousel/api/',             views.carousel_api,     name='carousel_api'),

    # Admin profile
    path('profile/', views.admin_profile, name='admin_profile'),
]
