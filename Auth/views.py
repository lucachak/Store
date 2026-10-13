from django import forms
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.translation import gettext as _
from django.utils.translation import gettext_lazy
from django.views import View

from Subscription.models import SubscriptionStatus

User = get_user_model()

PAGE_SIZE = 25


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Staff only. Signed-in users without staff access get a 403, not a redirect loop."""

    def test_func(self):
        return self.request.user.is_staff


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["first_name", "last_name"]
        labels = {
            "first_name": gettext_lazy("First name"),
            "last_name": gettext_lazy("Last name"),
        }


class AccountSettingsView(LoginRequiredMixin, View):
    """The signed-in user's own account page."""

    def get(self, request, *args, **kwargs):
        return self._render(request, ProfileForm(instance=request.user))

    def post(self, request, *args, **kwargs):
        form = ProfileForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, _("Your profile has been saved."))
            return redirect("account_settings")
        return self._render(request, form, status=400)

    @staticmethod
    def _render(request, form, status=200):
        email = request.user.emailaddress_set.filter(primary=True).first()
        context = {
            "form": form,
            "email_address": email,
            "has_two_factor": request.user.authenticator_set.exists(),
        }
        return render(request, "Auth/User/settings.html", context, status=status)


class UserListView(StaffRequiredMixin, View):
    """Searchable, paginated list of users. HTMX swaps just the table."""

    def get(self, request, *args, **kwargs):
        query = request.GET.get("q", "").strip()
        status = request.GET.get("status", "")

        users = User.objects.select_related(
            "usersubscription__subscription", "customer"
        ).order_by("-date_joined")
        if query:
            users = users.filter(
                Q(email__icontains=query)
                | Q(username__icontains=query)
                | Q(first_name__icontains=query)
                | Q(last_name__icontains=query)
            )
        if status == "none":
            users = users.filter(usersubscription__isnull=True)
        elif status in SubscriptionStatus.values:
            users = users.filter(usersubscription__status=status)

        page = Paginator(users, PAGE_SIZE).get_page(request.GET.get("page"))
        context = {
            "page": page,
            "q": query,
            "status": status,
            "statuses": SubscriptionStatus.choices,
        }
        template = "Auth/User/_user-table.html" if request.headers.get("HX-Request") else "Auth/User/user-list.html"
        return render(request, template, context)


class UserDetailsView(StaffRequiredMixin, View):
    def get(self, request, pk, *args, **kwargs):
        profile = get_object_or_404(
            User.objects.select_related("usersubscription__subscription", "customer"), pk=pk
        )
        return render(request, "Auth/User/user-details.html", {"profile": profile})
