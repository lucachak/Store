from django.shortcuts import render, redirect
from django.views import View 
from django.contrib.auth.decorators import login_required

from Subscription.models import SubscriptionPrice
# Create your views here.


class ProductPriceRedirectView(View):
    def get(self, request, obj_price_id=None, *args, **kwargs):
        request.session['checkout_session_price_id'] = obj_price_id
        return redirect("stripe-checkout-start")


@login_required
class CheckoutRedirectView(View):
    def get(self, request, *args, **kwargs):
        checkout_sub_price_id = request.session.get('checkout_session_price_id')

        try: 
            obj = SubscriptionPrice.objects.get(id=checkout_sub_price_id)
        except:
            obj = None

        if checkout_sub_price_id is None or obj is None :
            return redirect('subscription')
        checkout_sub_price_id = request.session.get('checkout_session_price_id')
        
        return redirect('/checkout')

class CheckoutFinalizeView(View):
    def get(self, request,  *args, **kwargs):
        pass