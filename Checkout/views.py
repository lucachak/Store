from django.shortcuts import render, redirect
from django.views import View 
from django.contrib.auth.decorators import login_required

# Create your views here.


class ProductPriceRedirectView(View):
    def get(self, request, obj_price_id=None, *args, **kwargs):
        request.session['checkout_session_price_id'] = obj_price_id
        return render("/checkout")


@login_required
class CheckoutRedirectView(View):
    def get(self, request, *args, **kwargs):
        checkout_sub_price_id = request.session.get('checkout_session_price_id')
        if checkout_sub_price_id is None:
            return redirect('')
        checkout_sub_price_id = request.session.get('checkout_session_price_id')
        
        return redirect('/checkout')

class CheckoutFinalizeView(View):
    def get(self, request,  *args, **kwargs):
        pass