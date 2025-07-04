from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
from django.views import View
from django.contrib.auth import get_user_model




LOGIN_URL = settings.LOGIN_REDIRECT_URL
User = get_user_model()


# Create your views here. 

# generate a list of ALL Users
class UserListView(View):
    def get(self,request, *args, **kwargs):
        
        user_list = User.objects.all() 


        context = {
            'user_list':user_list
        }

        return render(request, "Auth/User/user-list.html", context)    

    def post(self,request):
        context_manager = {}
        pass


# generate a list of Active Users
class UserActiveListView(View):
    def get(self, request, *args, **kwargs):
        context = {
            "object_list":User.objects.filter(is_active=True)
        }

        return render(request, "Auth/User/active-users.html", context)

    def post(self, request, *args, **kwargs):
        pass



# generate the SPECIFIC user's details
class UserDetailsView(View):

    def get(self, request,username=None, *args, **kwargs):


        user = request.user
        print(
            user.has_perm("Subscription.basic"),
            user.has_perm("Subscription.pro"),
            user.has_perm("Subscription.advanced"),
            )

        profile_user_obj = get_object_or_404(User, username=username)
        is_me = profile_user_obj == user

        context = {
            "object":profile_user_obj,
            "instance":profile_user_obj,
            "is_me":is_me,
        }
        
        return render(request, "Auth/User/user-details.html", context)

    
    def post(self, request, *args, **kwargs):
        context_manager = {}
        
        pass

# generate the Staffs views/list
class StaffView(View):

    @staff_member_required(login_url=LOGIN_URL)
    def get(self, request, *args, **kwargs):
        context_manager = {}
        return render(request, 'Auth/Staff/staff-view.html', context_manager)


    def post(self,request):
        context_manager = {}

        pass

class AdminView(View):

    def get(self, request, *args, **kwargs):
        context_manager = {}
        return render(request, 'Auth/Admin/admin-view.html', context_manager)


    def post(self,request):
        context_manager = {}

        pass


class ProfileListView(View):
    def get(self, request, username=None, *args, **kwargs):
        profile_obj = get_object_or_404(User,username=username)
        user = request.user
        if profile_obj == user:
            if user.has_perm("auth.view_user"):
                print("Good")

        context_manager = {
            "user":profile_obj,
            "is_me":True if profile_obj == request.user else False,
        }
        return render(request, 'Auth/userview.html', context_manager)


