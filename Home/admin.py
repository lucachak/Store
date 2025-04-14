from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import *
# Register your models here.


@admin.register(UsersCount)
class UserCount(ModelAdmin):
    pass