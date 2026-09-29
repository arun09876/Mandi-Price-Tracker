"""data.gov.in mandi price API client + pandas cleaning + upsert."""
import hashlib
import logging

import pandas as pd
import requests
from django.conf import settings
from django.core.cache import cache
from django.db import transaction

from .models import Commodity, Market, Price

log = logging.getLogger(__name__)

PAGE_SIZE = 1000
RAW_CACHE_TTL = 60 * 30
DISTRICT_ALIASES = {"Cuddapah": "Kadapa", "Chittor": "Chittoor", "Nellore": "Sri Potti Sriramulu Nellore",
                    "Vishakhapatnam": "Visakhapatnam", "Ananthapur": "Anantapur"}
# Keep display names short and consistent.
DISTRICT_DISPLAY = {"Sri Potti Sriramulu Nellore": "Nellore"}


class DataGovError(Exception):
    pass


def fetch_page(offset: int, state: str) -> list[dict]:
    """One API page. Raw responses are cached in Redis so Celery retries don't re-hit the API."""
    params = {
        "api-key": settings.DATA_GOV_API_KEY,
        "format": "json",
        "limit": PAGE_SIZE,
        "offset": offset,
        "filters[state.keyword]": state,
    }
    key = "mandi:raw:" + hashlib.sha1(f"{state}|{offset}|{pd.Timestamp.now():%Y%m%d%H}".encode()).hexdigest()
    cached = cache.get(key)
    if cached is not None:
        return cached
    resp = requests.get(settings.MANDI_API_URL, params=params, timeout=30)
    if resp.status_code != 200:
        raise DataGovError(f"data.gov.in returned HTTP {resp.status_code}: {resp.text[:200]}")
    body = resp.json()
    if "error" in body:  # e.g. {"error": "Rate limit exceeded"} or an invalid key
        raise DataGovError(f"data.gov.in: {body['error']}")
    records = body.get("records", [])
    cache.set(key, records, RAW_CACHE_TTL)
    return records


def fetch_all(state: str) -> list[dict]:
    if not settings.DATA_GOV_API_KEY:
        raise DataGovError("DATA_GOV_API_KEY is not set. Get a free key at https://data.gov.in")
    records, offset = [], 0
    while True:
        page = fetch_page(offset, state)
        records.extend(page)
        if len(page) < PAGE_SIZE:
            return records
        offset += PAGE_SIZE


def clean(records: list[dict], state: str) -> pd.DataFrame:
    """Raw API records -> tidy DataFrame (one row per day/market/commodity/variety)."""
    df = pd.DataFrame.from_records(records)
    if df.empty:
        return df
    df.columns = [c.lower().strip() for c in df.columns]
    df = df.rename(columns={"min_x0020_price": "min_price", "max_x0020_price": "max_price",
                            "modal_x0020_price": "modal_price", "arrival_x0020_date": "arrival_date"})
    for col in ("state", "district", "market", "commodity", "variety"):
        if col not in df.columns:
            df[col] = ""
        df[col] = df[col].fillna("").astype(str).str.strip().str.replace(r"\s+", " ", regex=True)
    df = df[df["state"].str.lower() == state.lower()]  # guard in case the API ignores the filter
    df["district"] = df["district"].replace(DISTRICT_ALIASES).replace(DISTRICT_DISPLAY)
    df["date"] = pd.to_datetime(df["arrival_date"], dayfirst=True, errors="coerce").dt.date
    for col in ("min_price", "max_price", "modal_price"):
        df[col] = pd.to_numeric(df[col], errors="coerce")
        df.loc[df[col] <= 0, col] = None
    df = df.dropna(subset=["date", "modal_price"])
    df = df[(df["modal_price"] > 0) & (df["modal_price"] < 1_000_000)]
    # Some rows have min/max swapped or zero — repair from the modal price.
    df["min_price"] = df[["min_price", "modal_price"]].min(axis=1).fillna(df["modal_price"])
    df["max_price"] = df[["max_price", "modal_price"]].max(axis=1).fillna(df["modal_price"])
    df[["min_price", "max_price", "modal_price"]] = df[["min_price", "max_price", "modal_price"]].round().astype(int)
    return df.drop_duplicates(subset=["date", "district", "market", "commodity", "variety"], keep="last")


@transaction.atomic
def save(df: pd.DataFrame, state: str) -> int:
    if df.empty:
        return 0
    commodities = {c.name: c for c in Commodity.objects.all()}
    for name in set(df["commodity"]) - commodities.keys():
        commodities[name] = Commodity.objects.create(name=name)

    markets = {(m.district, m.name): m for m in Market.objects.filter(state=state)}
    for district, name in set(zip(df["district"], df["market"])) - markets.keys():
        markets[(district, name)] = Market.objects.create(state=state, district=district, name=name)

    rows = [
        Price(date=r.date, market=markets[(r.district, r.market)], commodity=commodities[r.commodity],
              variety=r.variety, min_price=r.min_price, max_price=r.max_price, modal_price=r.modal_price)
        for r in df.itertuples()
    ]
    Price.objects.bulk_create(
        rows, batch_size=500, update_conflicts=True,
        unique_fields=["date", "market", "commodity", "variety"],
        update_fields=["min_price", "max_price", "modal_price"],
    )
    return len(rows)
