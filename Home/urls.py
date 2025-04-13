from django.contrib.auth.decorators import login_required
from django.urls import path
from . import views as v

urlpatterns = [
    path('',v.HomeView.as_view(),name="home"),
    path('protect/',login_required(v.ProtectedView.as_view()),name="protected")
]
