from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

User = get_user_model()


class StaffAccessTests(TestCase):
    def setUp(self):
        self.member = User.objects.create_user("member", "member@example.com", "pw-12345-pw")
        self.staff = User.objects.create_user("staff", "staff@example.com", "pw-12345-pw", is_staff=True)

    def test_anonymous_is_sent_to_login(self):
        for name, args in (("users_list", []), ("users_info_view", [self.member.pk]), ("account_settings", [])):
            response = self.client.get(reverse(name, args=args))
            self.assertEqual(response.status_code, 302, name)

    def test_member_cannot_list_or_view_users(self):
        self.client.force_login(self.member)
        self.assertEqual(self.client.get(reverse("users_list")).status_code, 403)
        self.assertEqual(self.client.get(reverse("users_info_view", args=[self.staff.pk])).status_code, 403)

    def test_staff_can_search_users(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("users_list"), {"q": "member"})
        self.assertContains(response, "member@example.com")
        self.assertNotContains(response, "staff@example.com</a>")

    def test_htmx_request_gets_only_the_table(self):
        self.client.force_login(self.staff)
        response = self.client.get(reverse("users_list"), HTTP_HX_REQUEST="true")
        self.assertNotContains(response, "<html")

    def test_profile_update(self):
        self.client.force_login(self.member)
        response = self.client.post(reverse("account_settings"), {"first_name": "Ana", "last_name": "Souza"})
        self.assertRedirects(response, reverse("account_settings"))
        self.member.refresh_from_db()
        self.assertEqual(self.member.get_full_name(), "Ana Souza")


class IdleLogoutTests(TestCase):
    @override_settings(SESSION_IDLE_TIMEOUT=60)
    def test_idle_session_is_ended(self):
        user = User.objects.create_user("ana", "ana@example.com", "pw-12345-pw")
        self.client.force_login(user)
        self.client.get(reverse("dashboard"))
        session = self.client.session
        session["last_activity"] -= 120
        session.save()
        response = self.client.get(reverse("dashboard"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.get(reverse("dashboard")).status_code, 302)
