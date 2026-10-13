from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from Home.models import UsersCount

User = get_user_model()


class HomeTests(TestCase):
    def test_landing_counts_visits_atomically(self):
        self.client.get(reverse("home"))
        self.client.get(reverse("home"))
        self.assertEqual(UsersCount.objects.get().counter, 2)

    def test_dashboard_requires_login(self):
        self.assertEqual(self.client.get(reverse("dashboard")).status_code, 302)

    def test_member_does_not_see_workspace_metrics(self):
        user = User.objects.create_user("ana", "ana@example.com", "pw-12345-pw")
        self.client.force_login(user)
        self.assertNotContains(self.client.get(reverse("dashboard")), "Workspace")

    def test_staff_sees_workspace_metrics(self):
        user = User.objects.create_user("st", "st@example.com", "pw-12345-pw", is_staff=True)
        self.client.force_login(user)
        self.assertContains(self.client.get(reverse("dashboard")), "Workspace")

    def test_custom_404(self):
        self.assertContains(self.client.get("/does-not-exist/"), "Page not found", status_code=404)
