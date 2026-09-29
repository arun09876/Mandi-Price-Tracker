import logging

import requests
from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Max
from django.template.loader import render_to_string
from django.utils import timezone

from . import datagov, i18n, queries
from .models import FetchLog, Price, PriceAlert

log = logging.getLogger(__name__)


@shared_task(bind=True, autoretry_for=(requests.RequestException,), retry_backoff=60, max_retries=3)
def fetch_daily_prices(self) -> dict:
    """Celery Beat, every morning: pull today's prices, store them, then check alerts."""
    run = FetchLog.objects.create()
    try:
        records = datagov.fetch_all(settings.MANDI_STATE)
        df = datagov.clean(records, settings.MANDI_STATE)
        saved = datagov.save(df, settings.MANDI_STATE)
        run.records, run.saved, run.ok = len(records), saved, True
        run.message = f"{saved} prices for {df['date'].nunique() if saved else 0} day(s)"
    except datagov.DataGovError as e:
        run.message = str(e)
        log.error("Mandi fetch failed: %s", e)
    finally:
        run.finished_at = timezone.now()
        run.save()
    if run.ok:
        queries.bump_version()
        check_alerts.delay()
    return {"ok": run.ok, "saved": run.saved}


@shared_task
def check_alerts() -> int:
    """Email each active alert at most once per day when its condition is met."""
    today = timezone.localdate()
    sent = 0
    alerts = PriceAlert.objects.filter(is_active=True).exclude(last_triggered_on=today).select_related("commodity")
    for alert in alerts:
        qs = Price.objects.filter(commodity=alert.commodity, market__district=alert.district)
        latest = qs.aggregate(d=Max("date"))["d"]
        if latest is None or (today - latest).days > 3:  # don't alert on stale data
            continue
        day = qs.filter(date=latest).select_related("market")
        if alert.condition == PriceAlert.Condition.ABOVE:
            hits = day.filter(modal_price__gte=alert.target_price).order_by("-modal_price")
        else:
            hits = day.filter(modal_price__lte=alert.target_price).order_by("modal_price")
        if not hits.exists():
            continue
        lang = alert.lang
        body = render_to_string("emails/price_alert.txt", {
            "alert": alert, "hits": hits[:5], "date": latest, "site_url": settings.SITE_URL,
            "crop": i18n.crop(alert.commodity.name, lang), "district": i18n.district(alert.district, lang),
            "lang": lang,
        })
        best = hits.first()
        subject = (f"{i18n.crop(alert.commodity.name, lang)}: ₹{best.modal_price}/qtl at {best.market.name}"
                   f" ({latest:%d %b})")
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL, [alert.email])
        alert.last_triggered_on = today
        alert.save(update_fields=["last_triggered_on"])
        sent += 1
    return sent
