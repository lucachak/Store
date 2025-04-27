from django.contrib.auth.decorators import login_required
from django.urls import path
from . import views as v



urlpatterns = [
    path("checkout/sub-price/<int:price_id>/", 
            v.ProductPriceRedirectView.as_view(),
            name='sub-price-checkout'
            ),
    
    path("checkout/start/", 
            v.CheckoutRedirectView.as_view(),
            name='stripe-checkout-start'
            ),
    
    path("checkout/success/", 
            v.CheckoutFinalizeView.as_view(),
            name='stripe-checkout-end'
            ),
]
