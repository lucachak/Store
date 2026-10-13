from django.contrib import admin
from unfold.admin import ModelAdmin, TabularInline

from .models import Subscription, SubscriptionPrice, UserSubscription


class SubscriptionPriceInline(TabularInline):
    model = SubscriptionPrice
    readonly_fields = ["stripe_id"]
    extra = 0
    can_delete = False


@admin.register(Subscription)
class SubscriptionAdmin(ModelAdmin):
    inlines = [SubscriptionPriceInline]
    list_display = ["name", "active", "featured", "order", "stripe_id"]
    list_filter = ["active"]
    readonly_fields = ["stripe_id"]
    filter_horizontal = ["groups", "permissions"]


@admin.register(UserSubscription)
class UserSubscriptionAdmin(ModelAdmin):
    list_display = ["user", "subscription", "status", "current_period_end", "cancel_at_period_end"]
    list_filter = ["status", "subscription"]
    search_fields = ["user__email", "user__username", "stripe_id"]
    readonly_fields = ["stripe_id"]
