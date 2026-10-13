from django.core.management.base import BaseCommand

from Subscription import services


class Command(BaseCommand):
    help = "Copy each active plan's permissions onto the plan's groups."

    def handle(self, *args, **options):
        services.sync_group_permissions()
        self.stdout.write(self.style.SUCCESS("Plan permissions synced to groups."))
