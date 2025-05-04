from django.contrib.auth.decorators import login_required
from django.urls import path
from . import views as v

urlpatterns = [
    path('',v.SubscriptionView.as_view(),name="pricing"),
    path('<str:interval>/', login_required(v.SubscriptionView.as_view()),name="subscription_inter"),
    path('accounts/billing/',login_required(v.UserSubscriptionView.as_view()), name='user_subscription'),
    path('accounts/billing/cancel', login_required(v.UserSubscriptionCancelView.as_view()), name='user_subscription_cancel'),
]
