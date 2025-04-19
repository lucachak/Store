from django.urls import path
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required

from . import views as v 

urlpatterns = [
    path('userInfo/',login_required(v.UserInfoView.as_view()), name="user_info"),
    path('userView/<str:username>', login_required(v.UserView.as_view()), name="user_view"),

    path('staffView/', staff_member_required(v.StaffView.as_view()), name='staff_view'),
    path('adminView/',staff_member_required(v.AdminView.as_view()), name="admin_view"),

    path('profileList/',v.ProfileListView.as_view(), name="profile_list")
]
