from django.urls import path
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required

from . import views as v 

urlpatterns = [
    path('userinfo/',v.UserInfoView.as_view(), name="user_info"),
    path('staffView/', staff_member_required(v.StaffView.as_view()), name='staff_view'),
    path('adminView/',v.AdminView.as_view(), name="admin_view"),
    path('userView/', v.UserView.as_view(), name="user_view"),
]