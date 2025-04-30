from django.contrib.auth.decorators import login_required
from django.urls import path
from . import views as v

urlpatterns = [
    path('',v.SubscriptionView.as_view(),name="pricing"),
    path('<str:interval>/',v.SubscriptionView.as_view(),name="subscription_inter"),
    path('accounts/billing/', v.UserSubscriptionView.as_view(), name='user_subscription'),
    path('accounts/billing/cancel', v.UserSubscriptionCancelView.as_view(), name='user_subscription_cancel'),
]
