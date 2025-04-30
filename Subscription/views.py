from django.shortcuts import render,redirect
from django.views import View
from django.urls import reverse 
from Subscription.models import *

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

class UserSubscriptionView(View):



    def get(self, request, *args, **kwargs):
        user_sub_obj, created = UserSubscription.objects.get_or_create(user=request.user)
        if request.method == "POST":
            self.post(self, request, *args, **kwargs)
        return render(request, 'Subscription/user-details-view.html', {"subscription": user_sub_obj})


    def post(self, request, *args, **kwargs):
            print("refresh sub")
            finished = subs_utils.refresh_active_users_subscriptions(user_ids=[request.user.id], active_only=False)
            if finished:
                messages.success(request, "Your plan details have been refreshed.")
            else:
                messages.error(request, "Your plan details have not been refreshed, please try again.")
            return redirect(user_sub_obj.get_absolute_url())


class UserSubscriptionCancelView(View):
    
    def get(self, request, *args, **kwargs):
        user_sub_obj, created = UserSubscription.objects.get_or_create(user=request.user)
        return render(request, 'Subscriptions/user-cancel-view.html', {"subscription": user_sub_obj})
    
    def post(self, request, *args, **kwargs):
        user_sub_obj, created = UserSubscription.objects.get_or_create(user=request.user)
        if request.method == "POST":
            if user_sub_obj.stripe_id and user_sub_obj.is_active_status:
                sub_data = helpers.billing.cancel_subscription(
                    user_sub_obj.stripe_id, 
                    reason="User wanted to end", 
                    feedback="other",
                    cancel_at_period_end=True,
                    raw=False)
                for k,v in sub_data.items():
                    setattr(user_sub_obj, k, v)
                user_sub_obj.save()
                messages.success(request, "Your plan has been cancelled.")
            return redirect(user_sub_obj.get_absolute_url())
        return render(request, 'Subscriptions/user-cancel-view.html', {"subscription": user_sub_obj})
# Create your views here.