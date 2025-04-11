from django.urls import path
from . import views as v 

urlpatterns = [
    path('Login/', v.LoginView.as_view(), name="Login"),
    path('Register/', v.RegisterView.as_view(), name="Register"),
]