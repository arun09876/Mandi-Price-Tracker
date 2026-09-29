"""Generate 30 days of realistic demo prices so the app works without an API key.

The rows go through the same clean() + save() pipeline as real API data.
"""
import random
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from mandi import datagov, queries

MARKETS = {
    "Guntur": ["Guntur", "Tenali", "Narasaraopet", "Mangalagiri"],
    "Krishna": ["Vijayawada", "Machilipatnam", "Nuzvid", "Gudivada"],
    "Kurnool": ["Kurnool", "Adoni", "Nandyal", "Yemmiganur"],
    "Chittoor": ["Madanapalli", "Palamaner", "Punganur", "Chittoor"],
    "East Godavari": ["Rajahmundry", "Kakinada", "Peddapuram", "Ravulapalem"],
}
CROPS = {  # base modal price ₹/quintal, daily volatility
    "Tomato": (1400, 0.08), "Onion": (2200, 0.04), "Dry Chillies": (14500, 0.02),
    "Cotton": (7100, 0.01), "Paddy(Dhan)(Common)": (2300, 0.005), "Groundnut": (6200, 0.015),
    "Maize": (2150, 0.01), "Turmeric": (13500, 0.02), "Green Chilli": (3200, 0.06), "Brinjal": (1800, 0.07),
}


class Command(BaseCommand):
    help = "Create 30 days of demo mandi prices (clearly synthetic) for local development."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=30)
        parser.add_argument("--seed", type=int, default=42)

    def handle(self, days, seed, **options):
        rng = random.Random(seed)
        today = timezone.localdate()
        state = settings.MANDI_STATE
        records = []
        for crop, (base, vol) in CROPS.items():
            level = {m: base * rng.uniform(0.9, 1.1) for ms in MARKETS.values() for m in ms}
            for day in range(days, -1, -1):
                date = today - timedelta(days=day)
                drift = rng.gauss(0, vol)
                for district, markets in MARKETS.items():
                    for market in markets:
                        if rng.random() < 0.15:  # not every market reports every day
                            continue
                        level[market] *= 1 + drift + rng.gauss(0, vol / 2)
                        modal = round(level[market], -1)
                        records.append({
                            "state": state, "district": district, "market": market, "commodity": crop,
                            "variety": "Other", "grade": "FAQ", "arrival_date": date.strftime("%d/%m/%Y"),
                            "min_price": str(round(modal * rng.uniform(0.8, 0.95), -1)),
                            "max_price": str(round(modal * rng.uniform(1.05, 1.2), -1)),
                            "modal_price": str(modal),
                        })
        df = datagov.clean(records, state)
        saved = datagov.save(df, state)
        queries.bump_version()
        if options.get("verbosity", 1):
            self.stdout.write(self.style.SUCCESS(f"Saved {saved} demo price rows for {len(MARKETS)} districts."))
