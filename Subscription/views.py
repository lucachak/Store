from django.shortcuts import render,redirect
from django.views import View
from django.urls import reverse 
from Subscription.models import SubscriptionPrice

# Create your views here.

class SubscriptionView(View):
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

        context_manager = {
            "obj_list":obj_list,
            "mo_url":mo_url,
            "yr_url":yr_url,
            "act":act,
        }
        
        return render(request,"Subscription/pricing.html",context_manager)

    def post(self,request, *args, **kwargs):
        pass
