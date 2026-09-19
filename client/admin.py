from django.contrib import admin

from .models import (
    User,
    Grievance,
    GrievanceAttachment,
    GrievanceStatusHistory,
    Notice,
    JobListing,
    CarouselImage,
    SavedNotice,
    SavedJobListing,
    NoticeView,
    NotificationPreference,
    Notification,
)


# ---------------------------------------------------------------------------
# Custom User
# ---------------------------------------------------------------------------

class UserAdmin(admin.ModelAdmin):
    list_display = ("email", "first_name", "last_name", "user_type", "is_active", "is_staff", "date_joined")
    list_filter = ("user_type", "is_active", "is_staff")
    search_fields = ("email", "first_name", "last_name", "username", "phone_number")
    ordering = ("-date_joined",)

admin.site.register(User, UserAdmin)


# ---------------------------------------------------------------------------
# Grievances
# ---------------------------------------------------------------------------

class GrievanceAttachmentInline(admin.TabularInline):
    model = GrievanceAttachment
    extra = 0


class GrievanceStatusHistoryInline(admin.TabularInline):
    model = GrievanceStatusHistory
    extra = 0
    readonly_fields = ("updated_at",)


class GrievanceAdmin(admin.ModelAdmin):
    list_display = ("subject", "user", "category", "priority", "status", "is_spam", "created_at")
    list_filter = ("status", "priority", "category", "is_spam")
    search_fields = ("subject", "description", "user__email")
    date_hierarchy = "created_at"
    inlines = [GrievanceAttachmentInline, GrievanceStatusHistoryInline]

admin.site.register(Grievance, GrievanceAdmin)


class GrievanceAttachmentAdmin(admin.ModelAdmin):
    list_display = ("id", "grievance", "filename", "uploaded_at")
    search_fields = ("grievance__subject",)

admin.site.register(GrievanceAttachment, GrievanceAttachmentAdmin)


class GrievanceStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ("grievance", "status", "updated_by", "updated_at")
    list_filter = ("status",)

admin.site.register(GrievanceStatusHistory, GrievanceStatusHistoryAdmin)


# ---------------------------------------------------------------------------
# Notices
# ---------------------------------------------------------------------------

class NoticeAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "issue_date", "created_by")
    list_filter = ("category",)
    search_fields = ("title", "description")
    date_hierarchy = "issue_date"

admin.site.register(Notice, NoticeAdmin)


class CarouselImageAdmin(admin.ModelAdmin):
    list_display = ("id", "caption", "order", "is_active", "created_at")
    list_filter = ("is_active",)
    ordering = ("order",)

admin.site.register(CarouselImage, CarouselImageAdmin)


class SavedNoticeAdmin(admin.ModelAdmin):
    list_display = ("user", "notice", "saved_at")

admin.site.register(SavedNotice, SavedNoticeAdmin)


class NoticeViewAdmin(admin.ModelAdmin):
    list_display = ("user", "notice", "viewed_at")
    date_hierarchy = "viewed_at"

admin.site.register(NoticeView, NoticeViewAdmin)


# ---------------------------------------------------------------------------
# Jobs
# ---------------------------------------------------------------------------

class JobListingAdmin(admin.ModelAdmin):
    list_display = ("job_title", "department", "deadline", "is_active", "status", "created_at")
    list_filter = ("is_active", "department")
    search_fields = ("job_title", "department", "department_location")
    date_hierarchy = "deadline"

admin.site.register(JobListing, JobListingAdmin)


class SavedJobListingAdmin(admin.ModelAdmin):
    list_display = ("user", "job", "saved_at")

admin.site.register(SavedJobListing, SavedJobListingAdmin)


# ---------------------------------------------------------------------------
# Notifications
# ---------------------------------------------------------------------------

class NotificationPreferenceAdmin(admin.ModelAdmin):
    list_display = ("user", "new_notices", "grievance_updates", "new_job_listings")

admin.site.register(NotificationPreference, NotificationPreferenceAdmin)


class NotificationAdmin(admin.ModelAdmin):
    list_display = ("title", "user", "type", "is_read", "created_at")
    list_filter = ("type", "is_read")
    search_fields = ("title", "body", "user__email")
    date_hierarchy = "created_at"

admin.site.register(Notification, NotificationAdmin)