from django.urls import path

from . import views as v

urlpatterns = [
    path("", v.SubscriptionView.as_view(), name="pricing"),
    path("billing/", v.UserSubscriptionView.as_view(), name="user_subscription"),
    path("billing/cancel/", v.UserSubscriptionCancelView.as_view(), name="user_subscription_cancel"),
    path("billing/resume/", v.UserSubscriptionResumeView.as_view(), name="user_subscription_resume"),
    path("billing/portal/", v.BillingPortalView.as_view(), name="billing_portal"),
    # Keep last: it would otherwise swallow the paths above.
    path("<str:interval>/", v.SubscriptionView.as_view(), name="subscription_inter"),
]
