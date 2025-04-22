from django.contrib.auth.decorators import login_required
from django.urls import path
from . import views as v

urlpatterns = [
    path('',v.SubscriptionView.as_view(),name="subscription"),
    path('<str:interval>/',v.SubscriptionView.as_view(),name="subscription_inter"),
]
