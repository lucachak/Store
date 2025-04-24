from django.views import View
from django.shortcuts import render, redirect 
from .models import *

# Create your views here.


# display the home/ intro to the main page content
class HomeView(View):
    def get(self, request, *args, **kwargs):
        # add to the main counter the number of access on the main page
        try:
            field_name = 'counter'
            obj = UsersCount.objects.first()
            user_visits = getattr(obj, field_name) + 1
        except:
            user_visits = 1 
            UsersCount.objects.create(counter=user_visits)

        UsersCount.objects.update(counter=user_visits) 


        context = {'user_visits' : user_visits}
        return render(request, "Home/home.html", context)


class DashboardView(View):
    def get(self, request, *args, **kwargs):
        context_manager = {}
        return render(request,"Home/dashboard.html",context_manager)
        

    def post(self, request, *args, **kwargs):
        pass


