from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.conf import settings
from django.views import View
from django.contrib.auth import get_user_model

LOGIN_URL = settings.LOGIN_REDIRECT_URL
User = get_user_model()


# Create your views here.
class UserView(View):

    def get(self, request, username=None, *args, **kwargs):
        profile_obj = get_object_or_404(User,username=username)
        

        context_manager = {
            "user":profile_obj,
            "is_me":True if profile_obj == request.user else False,
        }
        return render(request, 'Auth/userview.html', context_manager)


    def post(self,request):
        context_manager = {}
        pass


class UserInfoView(View):

    def get(self, request, *args, **kwargs):
        context_manager = {}

        try:
            user_id = request.user.id
            username = request.user.username
            email = request.user.email
            context_manager = {
                'user_id': user_id,
                'username': username,
                'email':email,
                #'perm': request.user.has_perm()
            }
        except:
            context_manager = {
                'user_id': 'AnonUser',
                'username': 'Undefined',
                'email':'Undefined',
            }

        else:
            email = request.user.email
            user_id = request.user.id
            context_manager = {
                'user_id': user_id,
                'username': 'undefined',
                'email':email,
            }
        return render(request, "Auth/userinfo.html", context_manager)

    def post(self, request, *args, **kwargs):
        context_manager = {}
        
        pass

class StaffView(View):


    @staff_member_required(login_url=LOGIN_URL)
    def get(self, request, *args, **kwargs):
        context_manager = {}
        return render(request, 'Auth/staffview.html', context_manager)


    def post(self,request):
        context_manager = {}

        pass

class AdminView(View):

    def get(self, request, *args, **kwargs):
        context_manager = {}
        return render(request, 'Auth/adminview.html', context_manager)


    def post(self,request):
        context_manager = {}

        pass
