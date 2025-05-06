from django.urls import path
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required

from . import views as v 

urlpatterns = [
    
    #Users section
    path('users/',
        login_required(v.UserListView.as_view()),name="users_list"),
    
    path('usersActive/',
        login_required(v.UserActiveListView.as_view()),name="active_users_view"),

    path('usersDetails/<str:username>/',
        login_required(v.UserDetailsView.as_view()),name="users_info_view"),



    #Staff section
    path('staff/',
        staff_member_required(v.StaffView.as_view()),name='staff_view'),
    path('staffDetail/<str:username>',
        staff_member_required(v.StaffView.as_view()),name='staff_view'),


    #Admin section
    path('adminView/',
        staff_member_required(v.AdminView.as_view()), name="admin_view"),
]
