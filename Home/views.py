from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import F
from django.shortcuts import render
from django.views import View

from Subscription.models import (
    Subscription,
    SubscriptionPrice,
    SubscriptionStatus,
    UserSubscription,
)

from .models import UsersCount

User = get_user_model()


class HomeView(View):
    """Public landing page."""

    def get(self, request, *args, **kwargs):
        counter, _created = UsersCount.objects.get_or_create(
            pk=1, defaults={"counter": 0, "path": "/"}
        )
        UsersCount.objects.filter(pk=counter.pk).update(counter=F("counter") + 1)

        plans = (
            SubscriptionPrice.objects.filter(
                featured=True,
                subscription__active=True,
                interval=SubscriptionPrice.IntervalChoices.MONTHLY,
            )
            .select_related("subscription")[:4]
        )
        return render(request, "Home/home.html", {"plans": plans})


class DashboardView(LoginRequiredMixin, View):
    """Signed-in overview. Staff also get workspace numbers."""

    def get(self, request, *args, **kwargs):
        record = (
            UserSubscription.objects.filter(user=request.user).select_related("subscription").first()
        )
        email = request.user.emailaddress_set.filter(primary=True).first()
        context = {
            "subscription": record,
            "email_verified": bool(email and email.verified),
            "has_two_factor": request.user.authenticator_set.exists(),
        }
        if request.user.is_staff:
            subscriptions = UserSubscription.objects
            context["metrics"] = {
                "users": User.objects.count(),
                "plans": Subscription.objects.filter(active=True).count(),
                "paying": subscriptions.by_active_trialing().count(),
                "past_due": subscriptions.filter(status=SubscriptionStatus.PAST_DUE).count(),
                "visits": UsersCount.objects.values_list("counter", flat=True).first() or 0,
            }
        return render(request, "Home/dashboard.html", context)
