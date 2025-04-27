from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline
from .models import *

# Register your models here.

class SubscriptionPrice(TabularInline):
    model = SubscriptionPrice
    readonly_fields = ['stripe_id']
    can_delete = False
    extra = 0


class SubscriptionAdmin(ModelAdmin):
    inlines = [SubscriptionPrice]
    list_display = ['name', 'active']
    readonly_fields = ['stripe_id']



admin.site.register(Subscription,SubscriptionAdmin)

@admin.register(UserSubscription)
class UserSubscription(ModelAdmin):
    pass




