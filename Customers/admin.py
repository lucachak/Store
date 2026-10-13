from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import Customer


@admin.register(Customer)
class CustomerAdmin(ModelAdmin):
    list_display = ["user", "stripe_id", "init_email_confirmed"]
    search_fields = ["user__email", "stripe_id"]
    readonly_fields = ["stripe_id"]
