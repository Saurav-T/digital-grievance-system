from datetime import datetime

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Notice, User


class NoticePublishingTests(TestCase):
    def test_public_notices_page_shows_admin_created_notice(self):
        user = User.objects.create_user(
            email="admin@example.com",
            password="secret123",
            first_name="Admin",
            last_name="User",
        )
        Notice.objects.create(
            title="Published from admin",
            description="This notice should appear publicly",
            issue_date=timezone.make_aware(datetime(2026, 7, 18, 10, 0)),
            created_by=user,
        )

        response = self.client.get(reverse("notices"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Published from admin")
