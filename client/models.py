from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.utils import timezone


# ---------------------------------------------------------------------------
# Custom User
# ---------------------------------------------------------------------------

GENDER_CHOICES = [
    ("Male", "Male"),
    ("Female", "Female"),
    ("Other", "Other"),
    ("Prefer not to say", "Prefer not to say"),
]

USER_TYPE_CHOICES = [
    ("Citizen", "Citizen"),
    ("Staff", "Staff"),
]


class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("user_type", "Staff")
        return self.create_user(email, password, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    # ── Identity ────────────────────────────────────────────────────────
    first_name   = models.CharField(max_length=100)
    last_name    = models.CharField(max_length=100)
    email        = models.EmailField(unique=True)
    username     = models.CharField(max_length=30, unique=True, null=True, blank=True)

    # ── Signup fields ───────────────────────────────────────────────────
    phone_number = models.CharField(max_length=20, blank=True)
    dob          = models.DateField(null=True, blank=True)
    gender       = models.CharField(max_length=20, choices=GENDER_CHOICES, blank=True)
    address      = models.CharField(max_length=255, blank=True)
    municipality = models.CharField(max_length=150, blank=True)
    profile_picture = models.ImageField(upload_to="profile_pictures/", null=True, blank=True)

    # ── Role / status ───────────────────────────────────────────────────
    user_type    = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default="Citizen")
    is_active    = models.BooleanField(default=True)
    is_staff     = models.BooleanField(default=False)
    date_joined  = models.DateTimeField(default=timezone.now)
    # last_login is provided automatically by AbstractBaseUser

    objects = UserManager()

    USERNAME_FIELD  = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    class Meta:
        db_table = "users"
        ordering = ["-date_joined"]

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    @property
    def avatar_url(self):
        return self.profile_picture.url if self.profile_picture else None

    @property
    def is_citizen(self):
        return self.user_type == "Citizen"

    def __str__(self):
        return self.email


# ---------------------------------------------------------------------------
# Category
# ---------------------------------------------------------------------------

class Category(models.Model):
    name        = models.CharField(max_length=100, unique=True)
    description = models.TextField(null=True, blank=True)
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table           = "categories"
        verbose_name_plural = "Categories"
        ordering           = ["name"]

    def __str__(self):
        return self.name


# ---------------------------------------------------------------------------
# Grievance
# ---------------------------------------------------------------------------

class Grievance(models.Model):
    PRIORITY_CHOICES = [
        ("Low",      "Low"),
        ("Medium",   "Medium"),
        ("High",     "High"),
        ("Critical", "Critical"),
    ]
    STATUS_CHOICES = [
        ("Pending",   "Pending"),
        ("In Review", "In Review"),
        ("Resolved",  "Resolved"),
        ("Rejected",  "Rejected"),
    ]

    user            = models.ForeignKey(User, on_delete=models.CASCADE,  related_name="grievances")
    category        = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, blank=True, related_name="grievances")
    subject         = models.CharField(max_length=255)
    description     = models.TextField()
    priority        = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default="Medium")
    status          = models.CharField(max_length=20, choices=STATUS_CHOICES,   default="Pending")
    location_url    = models.URLField(null=True, blank=True)
    attachment      = models.ImageField(upload_to="grievances/", null=True, blank=True)
    is_spam         = models.BooleanField(default=False)
    spam_score      = models.FloatField(default=0.0)
    resolution_note = models.TextField(null=True, blank=True)
    created_at      = models.DateTimeField(auto_now_add=True)
    updated_at      = models.DateTimeField(auto_now=True)
    resolved_at     = models.DateTimeField(null=True, blank=True)
    rejected_at     = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "grievances"
        ordering = ["-created_at"]

    def __str__(self):
        return self.subject

    @property
    def priority_colour(self):
        return {
            "Low":      "bg-green-100 text-green-700",
            "Medium":   "bg-yellow-100 text-yellow-700",
            "High":     "bg-orange-100 text-orange-700",
            "Critical": "bg-red-100 text-red-700",
        }.get(self.priority, "bg-gray-100 text-gray-700")

    @property
    def status_colour(self):
        return {
            "Pending":   "bg-blue-100 text-blue-700",
            "In Review": "bg-yellow-100 text-yellow-700",
            "Resolved":  "bg-green-100 text-green-700",
            "Rejected":  "bg-red-100 text-red-700",
        }.get(self.status, "bg-gray-100 text-gray-700")


# ---------------------------------------------------------------------------
# Notice
# ---------------------------------------------------------------------------

class Notice(models.Model):
    CATEGORY_CHOICES = [
        ("jobs",         "Jobs"),
        ("government",   "Government"),
        ("scholarships", "Scholarships"),
        ("events",       "Events"),
        ("general",      "General"),
    ]

    title       = models.CharField(max_length=255)
    description = models.TextField()
    category    = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default="general")
    image       = models.ImageField(upload_to="notices/", null=True, blank=True)
    issue_date  = models.DateTimeField()
    created_by  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="notices")
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notices"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


# ---------------------------------------------------------------------------
# JobListing
# ---------------------------------------------------------------------------

class JobListing(models.Model):
    job_title           = models.CharField(max_length=255)
    department          = models.CharField(max_length=150)
    department_location = models.CharField(max_length=255)
    issue_date          = models.DateField()
    deadline            = models.DateField()
    job_description     = models.TextField()
    age_requirement     = models.CharField(max_length=100)
    job_requirements     = models.TextField()
    contact_information = models.TextField()
    is_active           = models.BooleanField(default=True)
    created_by          = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="job_listings")
    created_at          = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "job_listings"
        ordering = ["-created_at"]

    def __str__(self):
        return self.job_title

    @property
    def status(self):
        today = timezone.now().date()
        if not self.is_active:
            return "Closed"
        if self.deadline < today:
            return "Expired"
        return "Active"

    @property
    def status_colour(self):
        return {
            "Active":  "bg-green-100 text-green-700",
            "Expired": "bg-yellow-100 text-yellow-700",
            "Closed":  "bg-red-100 text-red-700",
        }.get(self.status, "bg-gray-100 text-gray-700")


# ---------------------------------------------------------------------------
# GrievanceStatusHistory
# ---------------------------------------------------------------------------

class GrievanceStatusHistory(models.Model):
    grievance  = models.ForeignKey(Grievance, on_delete=models.CASCADE, related_name="status_history")
    status     = models.CharField(max_length=20)
    remarks    = models.TextField(null=True, blank=True)
    updated_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "grievance_status_history"
        ordering = ["updated_at"]

    def __str__(self):
        return f"#{self.grievance_id} → {self.status}"


# ---------------------------------------------------------------------------
# CarouselImage
# ---------------------------------------------------------------------------

class CarouselImage(models.Model):
    image      = models.ImageField(upload_to='carousel/')
    caption    = models.CharField(max_length=255, blank=True)
    order      = models.PositiveIntegerField(default=1)
    is_active  = models.BooleanField(default=True)
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, related_name='carousel_images')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'carousel_images'
        ordering = ['order', '-created_at']

    def __str__(self):
        return self.caption or f'Carousel Image #{self.id}'

    def delete(self, *args, **kwargs):
        import os
        if self.image and os.path.isfile(self.image.path):
            os.remove(self.image.path)
        super().delete(*args, **kwargs)


# ---------------------------------------------------------------------------
# Saved items, notice views, notification preferences
# ---------------------------------------------------------------------------

class SavedNotice(models.Model):
    user     = models.ForeignKey(User, on_delete=models.CASCADE, related_name="saved_notices")
    notice   = models.ForeignKey(Notice, on_delete=models.CASCADE, related_name="saved_by")
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "saved_notices"
        unique_together = ("user", "notice")
        ordering = ["-saved_at"]

    def __str__(self):
        return f"{self.user} saved {self.notice}"


class SavedJobListing(models.Model):
    user     = models.ForeignKey(User, on_delete=models.CASCADE, related_name="saved_jobs")
    job      = models.ForeignKey(JobListing, on_delete=models.CASCADE, related_name="saved_by")
    saved_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "saved_job_listings"
        unique_together = ("user", "job")
        ordering = ["-saved_at"]

    def __str__(self):
        return f"{self.user} saved {self.job}"


class NoticeView(models.Model):
    """Tracks each time a citizen opens a notice's detail page (for analytics)."""
    user      = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notice_views")
    notice    = models.ForeignKey(Notice, on_delete=models.CASCADE, related_name="views")
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notice_views"
        ordering = ["-viewed_at"]

    def __str__(self):
        return f"{self.user} viewed {self.notice} @ {self.viewed_at}"


class NotificationPreference(models.Model):
    user              = models.OneToOneField(User, on_delete=models.CASCADE, related_name="notification_pref")
    new_notices       = models.BooleanField(default=True)
    grievance_updates = models.BooleanField(default=True)
    new_job_listings  = models.BooleanField(default=True)

    class Meta:
        db_table = "notification_preferences"

    def __str__(self):
        return f"Notification preferences for {self.user}"