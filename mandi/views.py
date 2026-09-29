from django import forms
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from . import i18n, queries
from .models import Commodity, FetchLog, PriceAlert


class AlertForm(forms.ModelForm):
    class Meta:
        model = PriceAlert
        fields = ["email", "commodity", "district", "condition", "target_price"]


def _int(value):
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def home(request):
    lang = i18n.get_lang(request)
    districts = queries.districts()
    district = request.GET.get("district") or (districts[0] if districts else None)
    if district not in districts:
        district = districts[0] if districts else None
    crops = queries.commodities_in(district)
    crop_ids = [c[0] for c in crops]
    commodity_id = _int(request.GET.get("commodity"))
    if commodity_id not in crop_ids:
        commodity_id = crop_ids[0] if crop_ids else None

    data = queries.latest_prices(commodity_id, district) if commodity_id and district else {"date": None, "rows": []}
    commodity = Commodity.objects.filter(pk=commodity_id).first()
    return render(request, "mandi/home.html", {
        "districts": [(d, i18n.district(d, lang)) for d in districts],
        "crops": [(cid, i18n.crop(name, lang)) for cid, name in crops],
        "district": district,
        "district_label": i18n.district(district, lang) if district else "",
        "commodity": commodity,
        "crop_label": i18n.crop(commodity.name, lang) if commodity else "",
        "prices": data,
        "last_fetch": FetchLog.objects.filter(ok=True).first(),
        "alert_form": AlertForm(initial={"commodity": commodity_id, "district": district}),
    })


def trend_chart(request, commodity_id, district):
    commodity = get_object_or_404(Commodity, pk=commodity_id)
    png = queries.trend_chart(commodity.pk, district, commodity.name)
    return HttpResponse(png, content_type="image/png")


@require_POST
def create_alert(request):
    lang = i18n.get_lang(request)
    form = AlertForm(request.POST)
    if form.is_valid() and form.cleaned_data["district"] in queries.districts():
        alert = form.save(commit=False)
        alert.lang = lang
        alert.save()
        messages.success(request, i18n.t("alert_created", lang))
    else:
        messages.error(request, "; ".join(f"{k}: {v[0]}" for k, v in form.errors.items()) or "Invalid district")
    return redirect(f"/?commodity={request.POST.get('commodity', '')}&district={request.POST.get('district', '')}")


def unsubscribe(request, token):
    alert = get_object_or_404(PriceAlert, token=token)
    alert.is_active = False
    alert.save(update_fields=["is_active"])
    messages.info(request, i18n.t("unsubscribed", alert.lang))
    return redirect("home")


def set_language(request, lang):
    if lang in i18n.LANGS:
        request.session["lang"] = lang
    nxt = request.GET.get("next", "/")
    if not url_has_allowed_host_and_scheme(nxt, allowed_hosts={request.get_host()}):
        nxt = "/"
    return redirect(nxt)
