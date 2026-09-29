"""English/Telugu UI strings plus Telugu names for common crops and AP districts."""

LANGS = {"en": "English", "te": "తెలుగు"}

STRINGS = {
    "app_name": {"en": "Mandi Price Tracker", "te": "మండీ ధరల ట్రాకర్"},
    "tagline": {"en": "Check today's crop prices across markets in your district before you sell.",
                "te": "అమ్మే ముందు మీ జిల్లాలోని మార్కెట్లలో ఈరోజు పంట ధరలు చూడండి."},
    "crop": {"en": "Crop", "te": "పంట"},
    "district": {"en": "District", "te": "జిల్లా"},
    "show_prices": {"en": "Show prices", "te": "ధరలు చూపించు"},
    "market": {"en": "Market", "te": "మార్కెట్"},
    "variety": {"en": "Variety", "te": "రకం"},
    "min": {"en": "Min", "te": "కనిష్ఠ"},
    "max": {"en": "Max", "te": "గరిష్ఠ"},
    "modal": {"en": "Modal price", "te": "సాధారణ ధర"},
    "change": {"en": "Change", "te": "మార్పు"},
    "per_quintal": {"en": "₹ per quintal (100 kg)", "te": "₹ క్వింటాలుకు (100 కిలోలు)"},
    "prices_on": {"en": "Prices reported on", "te": "ధరలు నమోదైన తేదీ"},
    "best_market": {"en": "Best price", "te": "అత్యుత్తమ ధర"},
    "no_data": {"en": "No prices reported for this crop in this district recently.",
                "te": "ఈ జిల్లాలో ఈ పంటకు ఇటీవల ధరలు నమోదు కాలేదు."},
    "trend": {"en": "30-day price trend", "te": "30 రోజుల ధరల ధోరణి"},
    "alert_title": {"en": "Get a price alert by email", "te": "ఈమెయిల్ ద్వారా ధర హెచ్చరిక పొందండి"},
    "alert_help": {"en": "We check prices every morning and email you once a day when your target is reached.",
                   "te": "ప్రతి ఉదయం ధరలు చూసి, మీ లక్ష్య ధర వచ్చినప్పుడు రోజుకు ఒకసారి ఈమెయిల్ పంపుతాం."},
    "email": {"en": "Email", "te": "ఈమెయిల్"},
    "condition": {"en": "When", "te": "ఎప్పుడు"},
    "above": {"en": "Price goes above", "te": "ధర దీనికంటే ఎక్కువైతే"},
    "below": {"en": "Price goes below", "te": "ధర దీనికంటే తగ్గితే"},
    "target_price": {"en": "Target price (₹/quintal)", "te": "లక్ష్య ధర (₹/క్వింటాలు)"},
    "create_alert": {"en": "Create alert", "te": "హెచ్చరిక సృష్టించు"},
    "alert_created": {"en": "Alert created! We'll email you when the price condition is met.",
                      "te": "హెచ్చరిక సృష్టించబడింది! ధర షరతు నెరవేరినప్పుడు ఈమెయిల్ పంపుతాం."},
    "unsubscribed": {"en": "Alert stopped. You won't get more emails for it.",
                     "te": "హెచ్చరిక ఆపివేయబడింది. ఇకపై దీని కోసం ఈమెయిల్స్ రావు."},
    "last_update": {"en": "Last data update", "te": "చివరి డేటా నవీకరణ"},
    "source": {"en": "Source: Agmarknet via data.gov.in (OGD Platform India).",
               "te": "మూలం: Agmarknet, data.gov.in (OGD ప్లాట్‌ఫామ్ ఇండియా)."},
    "choose": {"en": "— choose —", "te": "— ఎంచుకోండి —"},
}

CROPS_TE = {
    "Paddy(Dhan)(Common)": "వరి (సాధారణ)", "Paddy(Dhan)(Basmati)": "వరి (బాస్మతి)", "Rice": "బియ్యం",
    "Tomato": "టమాటా", "Onion": "ఉల్లిపాయ", "Potato": "బంగాళదుంప", "Dry Chillies": "ఎండు మిర్చి",
    "Green Chilli": "పచ్చి మిర్చి", "Cotton": "పత్తి", "Groundnut": "వేరుశెనగ", "Maize": "మొక్కజొన్న",
    "Turmeric": "పసుపు", "Banana": "అరటి", "Banana - Green": "పచ్చి అరటి", "Brinjal": "వంకాయ",
    "Bengal Gram(Gram)(Whole)": "శనగలు", "Black Gram (Urd Beans)(Whole)": "మినుములు",
    "Green Gram (Moong)(Whole)": "పెసలు", "Arhar (Tur/Red Gram)(Whole)": "కందులు", "Coconut": "కొబ్బరి",
    "Mango": "మామిడి", "Lemon": "నిమ్మకాయ", "Cabbage": "క్యాబేజీ", "Bhindi(Ladies Finger)": "బెండకాయ",
    "Jowar(Sorghum)": "జొన్నలు", "Bajra(Pearl Millet/Cumbu)": "సజ్జలు", "Ragi (Finger Millet)": "రాగులు",
    "Sugarcane": "చెరకు", "Castor Seed": "ఆముదాలు", "Sunflower": "పొద్దుతిరుగుడు", "Cauliflower": "కాలీఫ్లవర్",
    "Carrot": "క్యారెట్", "Beetroot": "బీట్‌రూట్", "Bottle gourd": "సొరకాయ", "Bitter gourd": "కాకరకాయ",
    "Ridgeguard(Tori)": "బీరకాయ", "Drumstick": "మునగకాయ", "Tamarind Fruit": "చింతపండు", "Cashewnuts": "జీడిపప్పు",
    "Papaya": "బొప్పాయి", "Guava": "జామ", "Sweet Lime": "బత్తాయి", "Water Melon": "పుచ్చకాయ", "Ginger(Green)": "అల్లం",
    "Garlic": "వెల్లుల్లి", "Cucumbar(Kheera)": "దోసకాయ", "Beans": "బీన్స్", "Capsicum": "కాప్సికం",
}

DISTRICTS_TE = {
    "Anantapur": "అనంతపురం", "Chittoor": "చిత్తూరు", "East Godavari": "తూర్పు గోదావరి", "Guntur": "గుంటూరు",
    "Kadapa": "కడప", "Krishna": "కృష్ణా", "Kurnool": "కర్నూలు", "Nellore": "నెల్లూరు", "Prakasam": "ప్రకాశం",
    "Srikakulam": "శ్రీకాకుళం", "Visakhapatnam": "విశాఖపట్నం", "Vizianagaram": "విజయనగరం",
    "West Godavari": "పశ్చిమ గోదావరి", "NTR": "ఎన్టీఆర్", "Eluru": "ఏలూరు", "Kakinada": "కాకినాడ",
    "Palnadu": "పల్నాడు", "Bapatla": "బాపట్ల", "Nandyal": "నంద్యాల", "Tirupati": "తిరుపతి",
    "Annamayya": "అన్నమయ్య", "Sri Sathya Sai": "శ్రీ సత్యసాయి", "Anakapalli": "అనకాపల్లి",
    "Konaseema": "కోనసీమ", "Parvathipuram Manyam": "పార్వతీపురం మన్యం", "Alluri Sitharama Raju": "అల్లూరి సీతారామరాజు",
}


def t(key: str, lang: str) -> str:
    entry = STRINGS.get(key, {})
    return entry.get(lang) or entry.get("en") or key


def crop(name: str, lang: str) -> str:
    return CROPS_TE.get(name, name) if lang == "te" else name


def district(name: str, lang: str) -> str:
    return DISTRICTS_TE.get(name, name) if lang == "te" else name


def get_lang(request) -> str:
    lang = request.session.get("lang", "en")
    return lang if lang in LANGS else "en"


def language(request):
    lang = get_lang(request)
    return {"lang": lang, "LANGS": LANGS, "T": {k: v.get(lang) or v["en"] for k, v in STRINGS.items()}}
