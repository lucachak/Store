from django.views import View
from django.shortcuts import render, redirect 
from .models import *
from django.urls import reverse 
from Subscription.models import *
from django.contrib import messages

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

# display the dashboard view
class DashboardView(View):
    def get(self, request, *args, **kwargs):
        context_manager = {}
        return render(request,"Home/dashboard.html",context_manager)
        

    def post(self, request, *args, **kwargs):
        pass


class TestView(View):

    def get(self,request, interval="month", *args, **kwargs):
        base_qs = SubscriptionPrice.objects.filter(featured=True)

        interval_mo = SubscriptionPrice.IntervalChoices.MONTHLY
        interval_yr = SubscriptionPrice.IntervalChoices.YEARLY

        obj_list = base_qs.filter(interval=interval_mo)

        url_path_name = "subscription_inter"
        mo_url = reverse(url_path_name, kwargs={"interval":interval_mo})
        yr_url = reverse(url_path_name, kwargs={"interval":interval_yr})

        act = interval_mo 

        if interval == interval_yr:
            act = interval_yr
            obj_list = base_qs.filter(interval=interval_yr)

        context = {
            "obj_list":obj_list,
            "mo_url":mo_url,
            "yr_url":yr_url,
            "act":act,
        }
        return render(request, 'Test/pricing.html', context)

    def post(self, request, *args, **kwargs):
        pass

