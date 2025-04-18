from django.shortcuts import render
from django.contrib.auth.decorators import login_required

from django.views import View


# Create your views here.

class UserView(View):

    @login_required
    def get(self, request, *args, **kwargs):
        context_manager = {}
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
