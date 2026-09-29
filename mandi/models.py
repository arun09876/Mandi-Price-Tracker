import secrets

from django.db import models


class Commodity(models.Model):
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name_plural = "commodities"

    def __str__(self):
        return self.name


class Market(models.Model):
    state = models.CharField(max_length=60)
    district = models.CharField(max_length=80, db_index=True)
    name = models.CharField(max_length=120)

    class Meta:
        ordering = ["district", "name"]
        constraints = [models.UniqueConstraint(fields=["state", "district", "name"], name="uniq_market")]

    def __str__(self):
        return f"{self.name} ({self.district})"


class Price(models.Model):
    """One row per market/commodity/variety per day. Prices are ₹ per quintal."""

    date = models.DateField(db_index=True)
    market = models.ForeignKey(Market, on_delete=models.CASCADE, related_name="prices")
    commodity = models.ForeignKey(Commodity, on_delete=models.CASCADE, related_name="prices")
    variety = models.CharField(max_length=100, blank=True)
    min_price = models.PositiveIntegerField()
    max_price = models.PositiveIntegerField()
    modal_price = models.PositiveIntegerField()

    class Meta:
        ordering = ["-date", "-modal_price"]
        constraints = [
            models.UniqueConstraint(fields=["date", "market", "commodity", "variety"], name="uniq_daily_price")
        ]
        indexes = [models.Index(fields=["commodity", "date"])]

    def __str__(self):
        return f"{self.date} {self.commodity} @ {self.market}: ₹{self.modal_price}"


class PriceAlert(models.Model):
    class Condition(models.TextChoices):
        ABOVE = "above", "Price goes above"
        BELOW = "below", "Price goes below"

    email = models.EmailField()
    commodity = models.ForeignKey(Commodity, on_delete=models.CASCADE)
    district = models.CharField(max_length=80)
    condition = models.CharField(max_length=5, choices=Condition.choices, default=Condition.ABOVE)
    target_price = models.PositiveIntegerField(help_text="₹ per quintal")
    lang = models.CharField(max_length=2, default="en")
    is_active = models.BooleanField(default=True)
    last_triggered_on = models.DateField(null=True, blank=True)
    token = models.CharField(max_length=32, unique=True, default=secrets.token_urlsafe)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.email}: {self.commodity} {self.condition} ₹{self.target_price} in {self.district}"


class FetchLog(models.Model):
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    ok = models.BooleanField(default=False)
    records = models.PositiveIntegerField(default=0)
    saved = models.PositiveIntegerField(default=0)
    message = models.TextField(blank=True)

    class Meta:
        ordering = ["-started_at"]
