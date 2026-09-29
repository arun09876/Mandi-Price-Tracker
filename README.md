# Mandi Price Tracker

> Farmers often sell without knowing what nearby markets are paying. Pick a crop and district to see today's prices in every market, the 30-day trend, and set up an email alert for when your target price is reached. In English or Telugu.

**Stack:** Django · requests · pandas · Matplotlib · Celery Beat · Redis · Bootstrap 5

## Features

- **Crop + district selector**: today's min, max, and modal price (₹/quintal) for every market in the district, sorted best first, with the change since each market's previous report.
- **30-day trend chart** (Matplotlib): lines for the top five reporting markets, plus a dashed district average.
- **Email price alerts**: "Tell me when Dry Chillies in Guntur goes above ₹15,000". Each alert fires at most once a day, skips stale data (older than 3 days), and has a one-click unsubscribe link. It's sent in the user's language.
- **Celery Beat, every morning at 9:30 IST**: `fetch_daily_prices` pulls the state's records from data.gov.in (paginated), cleans them with pandas, upserts them, then chains `check_alerts`. It auto-retries network errors with backoff, and every run is recorded in a `FetchLog`.
- **Redis**:
  - Raw API pages are cached for 30 minutes, so Celery retries don't hammer the API.
  - Dropdowns, price tables, and charts are cached under a version key. A successful fetch bumps the version, which invalidates everything at once.
- **Telugu + English toggle**, including Telugu names for about 45 common crops and all AP districts, and Telugu alert emails.

### Why store daily snapshots?

The data.gov.in resource ([Current Daily Price of Various Commodities from Various Markets](https://www.data.gov.in/resource/current-daily-price-various-commodities-various-markets-mandi)) only returns **the current day's** prices. The 30-day trend exists because the Beat job saves a snapshot every morning (`UniqueConstraint(date, market, commodity, variety)` + `bulk_create(update_conflicts=True)`).

### pandas cleaning

The cleaning step handles:
- dd/mm/yyyy dates
- numeric coercion
- dropping zero or absurd prices
- repairing swapped or zero min/max values from the modal price
- normalising district spellings (`Cuddapah` → `Kadapa`)
- whitespace
- de-duplication
- re-filtering by state in case the API ignores the filter

## Run locally

```bash
python -m venv .venv && .venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
python manage.py seed_demo_prices     # 30 days of synthetic data for 5 AP districts, so the UI works immediately
python manage.py runserver
```

**Real data:** get a free API key at [data.gov.in](https://data.gov.in) (sign up → My Account → API key), put it in `.env` as `DATA_GOV_API_KEY`, then run:

```bash
python manage.py fetch_prices          # the same job Beat runs each morning
```

To try other states, change `MANDI_STATE`. For the full stack (Postgres, Redis, worker, beat), run `docker compose up --build`. To schedule locally:

```bash
celery -A config worker -l info --pool=solo
celery -A config beat -l info
```

> The demo seeder's prices are **synthetic**. Delete them before going live: `Price.objects.all().delete()` in `manage.py shell`.

## Tests

```bash
python manage.py test
```

The tests cover API pagination and filter params (mocked `requests`), a missing key being logged, cleaning rules, idempotent upsert, above/below alerts, once-per-day sending, stale-data suppression, Telugu email, best-market ordering, the chart PNG, the language toggle, and alert create/unsubscribe.
