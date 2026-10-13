from django.urls import path

from . import views as v

urlpatterns = [
    path("settings/", v.AccountSettingsView.as_view(), name="account_settings"),
    path("users/", v.UserListView.as_view(), name="users_list"),
    path("users/<int:pk>/", v.UserDetailsView.as_view(), name="users_info_view"),
]
