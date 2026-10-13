from django.core.management.base import BaseCommand

from Subscription import services


class Command(BaseCommand):
    help = "Refresh subscriptions from Stripe. Run it from cron as a safety net for missed webhooks."

    def add_arguments(self, parser):
        parser.add_argument("--all", action="store_true", help="Include subscriptions that are not active.")
        parser.add_argument(
            "--cancel-dangling",
            action="store_true",
            help="Cancel active Stripe subscriptions that have no local record.",
        )

    def handle(self, *args, **options):
        refreshed, total = services.refresh_active_subscriptions(active_only=not options["all"])
        self.stdout.write(f"Refreshed {refreshed} of {total} subscriptions.")
        if options["cancel_dangling"]:
            count = services.cancel_dangling_subscriptions()
            self.stdout.write(f"Cancelled {count} dangling subscriptions.")
