from django.urls import path
from . import views as v

urlpatterns = [
    path('',v.HomeView.as_view(),name="home")

]
