"""
URL configuration for Core project.
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.conf import settings
from django.urls import path,include
from django.contrib.auth.decorators import login_required
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),

    path('',include("Home.urls")), # Home App handles it
    path('auth/', include("Auth.urls")), # Auth app handles it 
    path('accounts/', include('allauth.urls')), # AllAuth external handles part of it
    path('checkout/', include('Checkout.urls')), # Deals with stripe and checkout sessions 
    path('subscription/',include('Subscription.urls')), # Subscription app handles it 
    
    path("__reload__/", include("django_browser_reload.urls")), # skip
    
]
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
