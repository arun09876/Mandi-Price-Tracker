from django.contrib import admin

from .models import Commodity, FetchLog, Market, Price, PriceAlert


@admin.register(Price)
class PriceAdmin(admin.ModelAdmin):
    list_display = ("date", "commodity", "market", "variety", "min_price", "max_price", "modal_price")
    list_filter = ("date", "market__district", "commodity")
    search_fields = ("market__name", "commodity__name")


@admin.register(PriceAlert)
class PriceAlertAdmin(admin.ModelAdmin):
    list_display = ("email", "commodity", "district", "condition", "target_price", "is_active", "last_triggered_on")
    list_filter = ("is_active", "condition")


@admin.register(FetchLog)
class FetchLogAdmin(admin.ModelAdmin):
    list_display = ("started_at", "ok", "records", "saved", "message")


admin.site.register(Market)
admin.site.register(Commodity)
