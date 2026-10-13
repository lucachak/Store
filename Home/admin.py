from django.contrib import admin
from unfold.admin import ModelAdmin

from .models import UsersCount


@admin.register(UsersCount)
class UsersCountAdmin(ModelAdmin):
    list_display = ["counter", "time_stamp"]
