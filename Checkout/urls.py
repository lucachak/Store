from django.urls import path

from . import views as v

urlpatterns = [
    path("plan/<int:price_id>/", v.CheckoutStartView.as_view(), name="sub-price-checkout"),
    path("success/", v.CheckoutFinalizeView.as_view(), name="stripe-checkout-end"),
    path("webhook/", v.StripeWebhookView.as_view(), name="stripe-webhook"),
]
