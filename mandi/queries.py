"""Read-side queries (cached in Redis) and the 30-day trend chart."""
import hashlib
import io
from datetime import timedelta

import matplotlib

matplotlib.use("Agg")
import matplotlib.dates as mdates  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402
from django.core.cache import cache  # noqa: E402
from django.db.models import Max  # noqa: E402

from .models import Market, Price  # noqa: E402

TTL = 60 * 60


def _version() -> int:
    return cache.get_or_set("mandi:ver", 1, None)


def bump_version():
    try:
        cache.incr("mandi:ver")
    except ValueError:
        cache.set("mandi:ver", 2, None)


def cached(name: str, build):
    key = f"mandi:v{_version()}:" + hashlib.sha1(name.encode()).hexdigest()
    value = cache.get(key)
    if value is None:
        value = build()
        cache.set(key, value, TTL)
    return value


def districts() -> list[str]:
    return cached("districts", lambda: list(Market.objects.values_list("district", flat=True).distinct().order_by("district")))


def commodities_in(district: str | None) -> list[tuple[int, str]]:
    def build():
        qs = Price.objects.all()
        if district:
            qs = qs.filter(market__district=district)
        return list(qs.values_list("commodity_id", "commodity__name").distinct().order_by("commodity__name"))
    return cached(f"commodities:{district}", build)


def latest_prices(commodity_id: int, district: str) -> dict:
    """Most recent day's prices for a crop across all markets in a district."""
    def build():
        qs = Price.objects.filter(commodity_id=commodity_id, market__district=district)
        latest = qs.aggregate(d=Max("date"))["d"]
        if latest is None:
            return {"date": None, "rows": []}
        rows = list(qs.filter(date=latest).select_related("market").order_by("-modal_price").values(
            "market__name", "variety", "min_price", "max_price", "modal_price"))
        # compare with each market's previous reported price
        prev = {}
        for p in qs.filter(date__lt=latest, date__gte=latest - timedelta(days=10)).order_by("date").values(
                "market__name", "variety", "modal_price"):
            prev[(p["market__name"], p["variety"])] = p["modal_price"]
        for r in rows:
            before = prev.get((r["market__name"], r["variety"]))
            r["change"] = r["modal_price"] - before if before else None
        return {"date": latest, "rows": rows}
    return cached(f"latest:{commodity_id}:{district}", build)


def trend_frame(commodity_id: int, district: str, days: int = 30) -> pd.DataFrame:
    qs = Price.objects.filter(commodity_id=commodity_id, market__district=district)
    latest = qs.aggregate(d=Max("date"))["d"]
    if latest is None:
        return pd.DataFrame()
    rows = qs.filter(date__gt=latest - timedelta(days=days)).values("date", "market__name", "modal_price")
    df = pd.DataFrame.from_records(rows).rename(columns={"market__name": "market"})
    return df.groupby(["date", "market"], as_index=False)["modal_price"].mean()


def trend_chart(commodity_id: int, district: str, title: str) -> bytes:
    def build():
        df = trend_frame(commodity_id, district)
        fig, ax = plt.subplots(figsize=(9, 4))
        if df.empty:
            ax.text(0.5, 0.5, "No price history yet", ha="center", va="center", color="#6c757d")
            ax.axis("off")
        else:
            df["date"] = pd.to_datetime(df["date"])
            top = df.groupby("market")["modal_price"].count().sort_values(ascending=False).head(5).index
            for market in top:
                s = df[df["market"] == market].sort_values("date")
                ax.plot(s["date"], s["modal_price"], marker="o", markersize=3, linewidth=1.8, label=market)
            avg = df.groupby("date")["modal_price"].mean()
            ax.plot(avg.index, avg.values, color="black", linestyle="--", linewidth=1.2, label="District average")
            ax.set_title(f"{title} — last 30 days (₹/quintal, modal price)")
            ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
            ax.grid(alpha=0.25)
            ax.spines[["top", "right"]].set_visible(False)
            ax.legend(fontsize=8, frameon=False, loc="upper left", bbox_to_anchor=(1, 1))
        fig.tight_layout()
        buf = io.BytesIO()
        fig.savefig(buf, format="png", dpi=110)
        plt.close(fig)
        return buf.getvalue()
    return cached(f"chart:{commodity_id}:{district}", build)
