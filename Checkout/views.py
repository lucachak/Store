from django.contrib.auth.decorators import login_required
from Subscription.models import SubscriptionPrice,Subscription, UserSubscription
from django.http import HttpResponseBadRequest
from django.contrib.auth import get_user_model
from django.shortcuts import redirect, render
from django.contrib import messages
from django.conf import settings
from django.urls import reverse
from django.views import View
import Core.billing


BASE_URL = settings.BASE_URL

# Create your views here.
User = get_user_model()

class ProductPriceRedirectView(View):
    def get(self, request, price_id=None, *args, **kwargs):
        request.session['checkout_subscription_price_id'] = price_id
        return redirect("stripe-checkout-start")


class CheckoutRedirectView(View):
    
    def get(self, request, *args, **kwargs):
        val = request.user.customer.stripe_id

        print(val)

        checkout_subscription_price_id = request.session.get('checkout_subscription_price_id')

        success_url_path = reverse('stripe-checkout-end')
        pricing_url_path = reverse('pricing')
        success_url = f'{BASE_URL}{success_url_path}'
        cancel_url = f'{BASE_URL}{pricing_url_path}'

        try: 
            obj = SubscriptionPrice.objects.get(id=checkout_subscription_price_id)
        except:
            obj = None

        if checkout_subscription_price_id is None or obj is None :
            return redirect('pricing')
        customer_id = request.user.customer.stripe_id
        
        price_stripe_id = obj.stripe_id
        
        url = Core.billing.start_checkout_session(customer_id, success_url=success_url, cancel_url=cancel_url,
                                                  price_stripe_id=price_stripe_id, raw=False)
        return redirect(url)

class CheckoutFinalizeView(View):
    def get(self, request,  *args, **kwargs):
        
        session_id  = request.GET.get('session_id')

        customer_id, plan_id, sub_stripe_id = Core.billing.get_checkout_customer_plan(session_id=session_id)
        
        #####################################################################################
        try:
            sub_obj = Subscription.objects.get(subscriptionprice__stripe_id=plan_id)
        except:
            sub_obj = None


        try:
            user_obj = User.objects.get(customer__stripe_id=customer_id)
        except:
            user_obj = None

        #####################################################################################
        _user_sub_exists = False 
        updated_sub_options = {
                "subscription": sub_obj,
                "stripe_id":sub_stripe_id,
                "user_cancelled":False
        }
        
        
        
        try:
            _user_sub_obj = UserSubscription.objects.get(user=user_obj)
            _user_sub_exists = True

        except UserSubscription.DoesNotExist:
            _user_sub_obj = UserSubscription.objects.create(
                user=user_obj,
                **updated_sub_options 
                )
        except:
            _user_sub_obj = None
        
        if None in [sub_obj, user_obj ,_user_sub_obj]:
            return HttpResponseBadRequest("There was an Internal Error. Please Contact Us.")

        if _user_sub_exists:
            # cancel old one
            old_stripe_id = _user_sub_obj.stripe_id

            if old_stripe_id is not None:
                Core.billing.cancel_subscription(old_stripe_id,reason="Auto Ended Membership, New Membership" ,feedback="other")

            #assing a new one  (sub) 
            for k, v in updated_sub_options.items():
                setattr(_user_sub_obj, k,v)

            _user_sub_obj.save()
        context = {}

        messages.success(request, "Profile details updated.")
        return render(request ,"Checkout/success.html", context)
