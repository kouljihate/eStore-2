CURRENCIES = {
    "MAD": {"symbol": "MAD", "name_en": "Moroccan Dirham", "name_ar": "درهم مغربي", "name_fr": "Dirham marocain"},
    "EUR": {"symbol": "\u20ac", "name_en": "Euro", "name_ar": "يورو", "name_fr": "Euro"},
    "USD": {"symbol": "$", "name_en": "US Dollar", "name_ar": "دولار", "name_fr": "Dollar américain"},
    "GBP": {"symbol": "\u00a3", "name_en": "British Pound", "name_ar": "جنيه إسترليني", "name_fr": "Livre sterling"},
}


def get_currency_code(page):
    code = page.session.store.get("currency")
    return code if code in CURRENCIES else "MAD"


def get_currency_symbol(page):
    return CURRENCIES.get(get_currency_code(page), CURRENCIES["MAD"])["symbol"]


def format_currency(amount, currency="MAD"):
    info = CURRENCIES.get(currency, CURRENCIES["MAD"])
    value = f"{amount:,.2f}"
    if currency == "MAD":
        return f"{value} {info['symbol']}"
    return f"{info['symbol']}{value}"