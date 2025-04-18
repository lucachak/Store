from django.contrib.auth.decorators import login_required
from django.urls import path
from . import views as v

urlpatterns = [
    path('',v.HomeView.as_view(),name="home"),
    #path('dashboard/',v.*.as_view(), name="dashboard"),
    #path('metrics/',v.*.as_view(), name="metrics"),
]
