from typing import Any
from django.core.management.base import BaseCommand

from Subscription.models import Subscription



class Command(BaseCommand):
    def handle(self, *args:Any, **kwargs:Any):
        query_set = Subscription.objects.filter(active=True)

        for obj in query_set:
            sub_perms = obj.permission.all()

            for group in obj.groups.all():
                group.permissions.set(sub_perms)