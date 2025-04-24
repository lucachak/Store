from django.shortcuts import redirect
from django.urls import reverse
from django.views import View
from django.conf import settings
from django.contrib.auth import get_user_model
from Subscription.models import SubscriptionPrice
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
        checkout_subscription_price_id = request.session.get('checkout_subscription_price_id')

        success_url_base = BASE_URL
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
        customer_stripe_id = request.user.customer.stripe_id
        
        price_stripe_id = obj.stripe_id
        
        
        url = Core.billing.start_checkout_session(customer_stripe_id,
                                            success_url=success_url,
                                            cancel_url=cancel_url,
                                            price_stripe_id=price_stripe_id,
                                            raw=False)
        return redirect(url)

class CheckoutFinalizeView(View):
    def get(self, request,  *args, **kwargs):
        pass
