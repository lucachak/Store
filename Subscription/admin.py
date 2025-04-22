from django.contrib import admin
from unfold.admin import StackedInline, TabularInline
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

@admin.register(UserSubscription)
class UserSubscription(ModelAdmin):
    pass


admin.site.register(Subscription,SubscriptionAdmin)
#admin.site.register(UserSubscription)



