from django.core.management.base import BaseCommand

from mandi.tasks import fetch_daily_prices


class Command(BaseCommand):
    help = "Fetch today's mandi prices from data.gov.in now (same job Celery Beat runs every morning)."

    def handle(self, *args, **options):
        result = fetch_daily_prices.apply().get()
        style = self.style.SUCCESS if result["ok"] else self.style.ERROR
        self.stdout.write(style(f"ok={result['ok']} saved={result['saved']} (see FetchLog in admin for details)"))
