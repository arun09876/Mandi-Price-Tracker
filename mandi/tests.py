from datetime import timedelta
from unittest import mock

from django.core import mail
from django.core.cache import cache
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from . import datagov
from .models import Commodity, FetchLog, Price, PriceAlert
from .tasks import check_alerts, fetch_daily_prices

STATE = "Andhra Pradesh"


def record(market="Guntur", district="Guntur", commodity="Dry Chillies", modal="14500", date=None, **kw):
    date = date or timezone.localdate()
    r = {"state": STATE, "district": district, "market": market, "commodity": commodity, "variety": "Other",
         "grade": "FAQ", "arrival_date": date.strftime("%d/%m/%Y"), "min_price": "13000", "max_price": "15500",
         "modal_price": modal}
    r.update(kw)
    return r


class CleanSaveTests(TestCase):
    def test_clean_normalises_and_filters(self):
        rows = [
            record(),
            record(market="Tenali", modal="0"),                     # zero price dropped
            record(state="Telangana", district="Khammam"),          # other state dropped
            record(district="Cuddapah", market="Kadapa"),           # alias fixed
            {**record(market="Narasaraopet"), "min_price": "16000"},  # min > modal repaired
        ]
        df = datagov.clean(rows, STATE)
        self.assertEqual(sorted(df["market"]), ["Guntur", "Kadapa", "Narasaraopet"])
        self.assertIn("Kadapa", set(df["district"]))
        self.assertTrue((df["min_price"] <= df["modal_price"]).all())

    def test_save_is_idempotent_upsert(self):
        df = datagov.clean([record()], STATE)
        datagov.save(df, STATE)
        datagov.save(datagov.clean([record(modal="15000")], STATE), STATE)
        self.assertEqual(Price.objects.count(), 1)
        self.assertEqual(Price.objects.get().modal_price, 15000)


class FakeResponse:
    def __init__(self, records):
        self.status_code, self._records, self.text = 200, records, ""

    def json(self):
        return {"records": self._records}


@override_settings(DATA_GOV_API_KEY="test-key")
class FetchTaskTests(TestCase):
    def setUp(self):
        cache.clear()

    @mock.patch.object(datagov, "PAGE_SIZE", 2)
    @mock.patch("mandi.datagov.requests.get")
    def test_paginates_saves_and_logs(self, get):
        pages = [[record(), record(market="Tenali")], [record(market="Mangalagiri")]]
        get.side_effect = lambda url, params, timeout: FakeResponse(pages[params["offset"] // 2])
        result = fetch_daily_prices.apply().get()
        self.assertEqual(result, {"ok": True, "saved": 3})
        self.assertEqual(get.call_count, 2)
        self.assertEqual(get.call_args.kwargs["params"]["filters[state.keyword]"], STATE)
        self.assertTrue(FetchLog.objects.get().ok)

    @override_settings(DATA_GOV_API_KEY="")
    def test_missing_key_is_logged_not_raised(self):
        result = fetch_daily_prices.apply().get()
        self.assertFalse(result["ok"])
        self.assertIn("DATA_GOV_API_KEY", FetchLog.objects.get().message)


class AlertTests(TestCase):
    def setUp(self):
        datagov.save(datagov.clean([record(modal="14500"), record(market="Tenali", modal="15200")], STATE), STATE)
        self.chilli = Commodity.objects.get(name="Dry Chillies")

    def make_alert(self, **kw):
        defaults = dict(email="farmer@example.com", commodity=self.chilli, district="Guntur",
                        condition="above", target_price=15000)
        defaults.update(kw)
        return PriceAlert.objects.create(**defaults)

    def test_above_alert_sends_once_per_day(self):
        self.make_alert()
        self.assertEqual(check_alerts(), 1)
        self.assertEqual(check_alerts(), 0)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("Tenali", mail.outbox[0].subject)
        self.assertIn("/alerts/stop/", mail.outbox[0].body)

    def test_below_and_unmet(self):
        self.make_alert(condition="below", target_price=14000)
        self.assertEqual(check_alerts(), 0)

    def test_telugu_email(self):
        self.make_alert(lang="te")
        check_alerts()
        self.assertIn("ఎండు మిర్చి", mail.outbox[0].subject)

    def test_stale_data_does_not_alert(self):
        Price.objects.update(date=timezone.localdate() - timedelta(days=10))
        self.make_alert()
        self.assertEqual(check_alerts(), 0)


class ViewTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo_prices", days=10, verbosity=0)

    def setUp(self):
        cache.clear()

    def test_home_shows_best_market_first(self):
        tomato = Commodity.objects.get(name="Tomato")
        resp = self.client.get(reverse("home"), {"district": "Guntur", "commodity": tomato.pk})
        rows = resp.context["prices"]["rows"]
        self.assertGreater(len(rows), 0)
        self.assertEqual(rows[0]["modal_price"], max(r["modal_price"] for r in rows))
        self.assertContains(resp, "Best price")

    def test_invalid_params_fall_back(self):
        resp = self.client.get(reverse("home"), {"district": "Nowhere", "commodity": "abc"})
        self.assertEqual(resp.status_code, 200)

    def test_trend_chart_png(self):
        tomato = Commodity.objects.get(name="Tomato")
        resp = self.client.get(reverse("trend_chart", args=[tomato.pk, "East Godavari"]))
        self.assertEqual(resp["Content-Type"], "image/png")
        self.assertTrue(resp.content.startswith(b"\x89PNG"))

    def test_telugu_toggle(self):
        self.client.get(reverse("set_language", args=["te"]))
        self.assertContains(self.client.get(reverse("home"), {"district": "Guntur"}), "గుంటూరు")

    def test_create_and_stop_alert(self):
        tomato = Commodity.objects.get(name="Tomato")
        self.client.post(reverse("create_alert"), {"email": "a@b.com", "commodity": tomato.pk, "district": "Guntur",
                                                   "condition": "above", "target_price": 2000})
        alert = PriceAlert.objects.get()
        self.client.get(reverse("unsubscribe", args=[alert.token]))
        alert.refresh_from_db()
        self.assertFalse(alert.is_active)
