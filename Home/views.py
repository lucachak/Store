from django.views import View
from django.shortcuts import render, redirect 
from .models import *

# Create your views here.


class HomeView(View):
    def get(self, request):
        UsersCount.objects.create()
        user_visits = UsersCount.objects.all().count() 

        context = {'user_visits' : user_visits}
        return render(request, "Home/home.html", context)


class ProtectedView(View):
    def get(self,request):
       return render(request, "Home/protected.html")
