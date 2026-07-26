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
# Grievance Categories
# ---------------------------------------------------------------------------
# Fixed government-service categories. Kept as a CharField + choices (same
# pattern as Notice.category) rather than a separate Category table, since
# these are predefined and don't need to be created/renamed from the admin
# panel. Add/remove entries here and the dropdown, badges, and filters
# everywhere in the app update automatically.

GRIEVANCE_CATEGORY_STYLES = {
    "administrative_services": ("Administrative Services",     "bg-slate-100 text-slate-700"),
    "citizenship_passport":    ("Citizenship & Passport",      "bg-blue-100 text-blue-700"),
    "ward_office_services":    ("Ward Office Services",        "bg-cyan-100 text-cyan-700"),
    "municipality_services":   ("Municipality Services",       "bg-indigo-100 text-indigo-700"),
    "roads_infrastructure":    ("Roads & Infrastructure",      "bg-amber-100 text-amber-700"),
    "drinking_water":          ("Drinking Water",               "bg-sky-100 text-sky-700"),
    "electricity":             ("Electricity",                  "bg-yellow-100 text-yellow-700"),
    "health_services":         ("Health Services",              "bg-red-100 text-red-700"),
    "education":               ("Education",                    "bg-purple-100 text-purple-700"),
    "agriculture":             ("Agriculture",                  "bg-green-100 text-green-700"),
    "land_revenue_survey":     ("Land Revenue & Survey",         "bg-lime-100 text-lime-700"),
    "police_services":         ("Police Services",               "bg-gray-200 text-gray-800"),
    "transport_management":    ("Transport Management",          "bg-orange-100 text-orange-700"),
    "social_security":         ("Social Security Allowance",     "bg-pink-100 text-pink-700"),
    "environment":             ("Environment",                   "bg-emerald-100 text-emerald-700"),
    "corruption_misconduct":   ("Corruption / Misconduct",       "bg-rose-100 text-rose-700"),
    "online_services":         ("Online Government Services",    "bg-violet-100 text-violet-700"),
    "disaster_relief":         ("Disaster Relief",               "bg-red-200 text-red-800"),
    "other":                   ("Other",                         "bg-gray-100 text-gray-600"),
}


def grievance_category_meta(category):
    """Return (label, pill_colour_classes) for a Grievance category slug,
    falling back gracefully for unrecognised/legacy values."""
    return GRIEVANCE_CATEGORY_STYLES.get(
        category,
        (category.replace("_", " ").title() or "Other", "bg-gray-100 text-gray-600"),
    )


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
    CATEGORY_CHOICES = [(slug, meta[0]) for slug, meta in GRIEVANCE_CATEGORY_STYLES.items()]

    user            = models.ForeignKey(User, on_delete=models.CASCADE,  related_name="grievances")
    category        = models.CharField(max_length=40, choices=CATEGORY_CHOICES, default="other")
    subject         = models.CharField(max_length=255)
    description     = models.TextField()
    priority        = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default="Medium")
    status          = models.CharField(max_length=20, choices=STATUS_CHOICES,   default="Pending")
    location_url    = models.CharField(max_length=255, null=True, blank=True)  # stores "lat, lng"
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
    def category_label(self):
        return grievance_category_meta(self.category)[0]

    @property
    def category_colour(self):
        return grievance_category_meta(self.category)[1]

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

# Each entry: slug -> (display label, Tailwind pill classes).
# Used for the admin "Add/Edit Notice" category dropdown and for rendering
# the small category pill on notice cards / the notice detail page.
NOTICE_CATEGORY_STYLES = {
    "general":              ("General Notice",        "bg-gray-100 text-gray-700"),
    "public_announcement":  ("Public Announcement",    "bg-blue-100 text-blue-700"),
    "emergency_alert":      ("Emergency Alert",        "bg-red-100 text-red-700"),
    "government_circular":  ("Government Circular",    "bg-indigo-100 text-indigo-700"),
    "tender_procurement":   ("Tender & Procurement",   "bg-amber-100 text-amber-700"),
    "vacancy_job":          ("Vacancy / Job Notice",   "bg-green-100 text-green-700"),
    "examination_notice":   ("Examination Notice",     "bg-purple-100 text-purple-700"),
    "meeting_notice":       ("Meeting Notice",         "bg-cyan-100 text-cyan-700"),
    "holiday_notice":       ("Holiday Notice",         "bg-pink-100 text-pink-700"),
    "policy_regulation":    ("Policy & Regulation",    "bg-slate-100 text-slate-700"),
    "citizen_services":     ("Citizen Services",       "bg-teal-100 text-teal-700"),
    "health_advisory":      ("Health Advisory",        "bg-rose-100 text-rose-700"),
    "press_release":        ("Press Release",          "bg-orange-100 text-orange-700"),
    "other":                ("Other",                  "bg-gray-100 text-gray-500"),
}


def notice_category_meta(category):
    """Return (label, pill_colour_classes) for a Notice category slug,
    falling back gracefully for unrecognised/legacy values."""
    return NOTICE_CATEGORY_STYLES.get(category, (category.replace("_", " ").title() or "Other", "bg-gray-100 text-gray-500"))


class Notice(models.Model):
    CATEGORY_CHOICES = [(slug, meta[0]) for slug, meta in NOTICE_CATEGORY_STYLES.items()]

    title       = models.CharField(max_length=255)
    description = models.TextField()
    category    = models.CharField(max_length=30, choices=CATEGORY_CHOICES, default="general")
    image       = models.ImageField(upload_to="notices/", null=True, blank=True)
    issue_date  = models.DateTimeField(auto_now_add=True)
    created_by  = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="notices")
    created_at  = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notices"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    @property
    def category_label(self):
        return notice_category_meta(self.category)[0]

    @property
    def category_colour(self):
        return notice_category_meta(self.category)[1]


# ---------------------------------------------------------------------------
# JobListing
# ---------------------------------------------------------------------------

class JobListing(models.Model):
    job_title           = models.CharField(max_length=255)
    department          = models.CharField(max_length=150)
    department_location = models.CharField(max_length=255)
    issue_date          = models.DateField(auto_now_add=True)
    deadline            = models.DateField()
    job_description     = models.TextField()
    age_requirement     = models.CharField(max_length=100)
    job_requirements     = models.TextField()
    contact_information = models.TextField()
    contact_email        = models.EmailField(blank=True, null=True)
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


# ---------------------------------------------------------------------------
# Notification (real, DB-backed — powers the header bell + /notifications/)
# ---------------------------------------------------------------------------

class Notification(models.Model):
    TYPE_CHOICES = [
        ("grievance", "Grievance"),
        ("job", "Job"),
        ("notice", "Notice"),
    ]

    user       = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    type       = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title      = models.CharField(max_length=255)
    body       = models.CharField(max_length=500, blank=True)
    url        = models.CharField(max_length=255, blank=True, default="#")
    is_read    = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    # Optional links back to the source record. Set to CASCADE so that
    # deleting a Notice/JobListing/Grievance automatically removes every
    # notification that was generated from it — no extra cleanup code needed
    # in the delete views.
    related_notice    = models.ForeignKey(Notice, on_delete=models.CASCADE, null=True, blank=True, related_name="notifications_for")
    related_job       = models.ForeignKey(JobListing, on_delete=models.CASCADE, null=True, blank=True, related_name="notifications_for")
    related_grievance = models.ForeignKey(Grievance, on_delete=models.CASCADE, null=True, blank=True, related_name="notifications_for")

    class Meta:
        db_table = "notifications"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_read"]),
            models.Index(fields=["user", "created_at"]),
        ]

    def __str__(self):
        return f"[{self.type}] {self.title} → {self.user}"


# Friendly labels for each grievance status, used when composing notification text.
GRIEVANCE_STATUS_LABELS = {
    "Pending":   "Submitted",
    "In Review": "Accepted for Review",
    "Resolved":  "Resolved",
    "Rejected":  "Rejected",
}


def _notif_pref_allows(user, ntype):
    """Return True if user currently has this notification type enabled
    (defaults to True if no preference row exists yet)."""
    pref = NotificationPreference.objects.filter(user=user).first()
    if not pref:
        return True
    return {
        "grievance": pref.grievance_updates,
        "notice": pref.new_notices,
        "job": pref.new_job_listings,
    }.get(ntype, True)


def create_notification(user, ntype, title, body="", url="#",
                         related_notice=None, related_job=None, related_grievance=None):
    """Create a single Notification for user, respecting their preference
    toggle for this type. Returns the created Notification, or None if the
    user has this notification type disabled."""
    if not _notif_pref_allows(user, ntype):
        return None
    return Notification.objects.create(
        user=user, type=ntype, title=title[:255], body=(body or "")[:500], url=url or "#",
        related_notice=related_notice, related_job=related_job, related_grievance=related_grievance,
    )


def notify_grievance_status(grievance, status):
    """Notify a grievance's owner that its status is now status
    (one of Grievance.STATUS_CHOICES), respecting their preference."""
    from django.urls import reverse
    label = GRIEVANCE_STATUS_LABELS.get(status, status)
    subject = grievance.subject
    url = reverse("grievance_detail", args=[grievance.id])

    if status == "Pending":
        title = "Grievance Submitted"
        body = f'Your grievance "{subject}" has been submitted and is pending review.'
    elif status == "In Review":
        title = "Grievance Accepted for Review"
        body = f'Your grievance "{subject}" has been accepted and is now under review.'
    elif status == "Resolved":
        title = "Grievance Resolved"
        note = f" {grievance.resolution_note}" if grievance.resolution_note else ""
        body = f'Your grievance "{subject}" has been resolved.{note}'
    elif status == "Rejected":
        title = "Grievance Rejected"
        note = f" Reason: {grievance.resolution_note}" if grievance.resolution_note else ""
        body = f'Your grievance "{subject}" has been rejected.{note}'
    else:
        title = f"Grievance Status: {label}"
        body = f'Your grievance "{subject}" status changed to {label}.'

    return create_notification(grievance.user, "grievance", title, body, url, related_grievance=grievance)


def notify_all_citizens(ntype, title, body="", url="#", related_notice=None, related_job=None):
    """Broadcast a notification (new notice / new job listing) to every
    active citizen who currently has this notification type enabled."""
    citizens = User.objects.filter(user_type="Citizen", is_active=True)
    prefs_by_user = {
        p.user_id: p
        for p in NotificationPreference.objects.filter(user__in=citizens)
    }
    field = {"notice": "new_notices", "job": "new_job_listings"}.get(ntype, None)

    to_create = []
    for u in citizens:
        pref = prefs_by_user.get(u.id)
        enabled = getattr(pref, field, True) if (pref and field) else True
        if enabled:
            to_create.append(Notification(
                user=u, type=ntype, title=title[:255], body=(body or "")[:500], url=url or "#",
                related_notice=related_notice, related_job=related_job,
            ))
    if to_create:
        Notification.objects.bulk_create(to_create)
    return len(to_create)