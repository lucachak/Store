from django.contrib import admin
from django.conf import settings
from django.urls import path,include
from django.conf.urls.static import static
from django.contrib.auth.decorators import login_required

urlpatterns = [
    path('admin/', admin.site.urls),

    path('',include("Home.urls")), # Home App handles it
    path('auth/', include("Auth.urls")), # Auth app handles it 
    path('accounts/',include('allauth.urls')), # AllAuth external handles part of it
    path('checkout/', include('Checkout.urls')), # Deals with stripe and checkout sessions 
    path('subscription/',include('Subscription.urls')), # Subscription app handles it 
    path("__reload__/", include("django_browser_reload.urls")), # skip
    
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
