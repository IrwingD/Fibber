"""
faker_api.py
Wraps the Faker library: discovers available providers per locale,
and generates rows/streams of synthetic data from a JSON schema.

Schema shape (sent from the frontend):
    fields = [
        {"name": "full_name", "provider": "name"},
        {"name": "email", "provider": "email"},
        ...
    ]
"""

import inspect
from faker import Faker

# A curated subset of Faker's ~100 locales -- enough variety without
# overwhelming a dropdown. Add more codes here if you need them; Faker
# supports them all, this list is just what the UI offers.
COMMON_LOCALES = [
    "en_US", "en_GB", "en_IN", "de_DE", "fr_FR", "es_ES", "it_IT",
    "pt_BR", "nl_NL", "ru_RU", "ja_JP", "zh_CN", "ko_KR", "ar_AA",
    "hi_IN", "tr_TR", "pl_PL", "sv_SE",
]

# Generic BaseProvider helpers that exist on every Faker instance but
# aren't meaningful "data fields" on their own (they're building blocks
# other providers use internally). Hide these from the field picker.
EXCLUDE = {
    "seed_instance", "seed", "format", "parse", "add_provider", "provider",
    "get_formatter", "set_formatter", "set_arguments", "optional", "unique",
    "random", "items", "get_words_list", "random_choices", "random_sample",
    "random_elements", "random_int", "random_number", "random_digit",
    "random_digit_not_null", "random_digit_or_empty",
    "random_digit_not_null_or_empty", "random_letter", "random_letters",
    "random_lowercase_letter", "random_uppercase_letter",
    "randomize_nb_elements", "numerify", "lexify", "bothify", "locales",
    "locale", "providers", "factories", "weights", "del_arguments",
}

# Best-effort keyword categorization so the field picker can group
# ~200 provider methods instead of dumping one giant alphabetical list.
CATEGORY_KEYWORDS = [
    ("person", ["name", "first_name", "last_name", "prefix", "suffix", "username"]),
    ("internet", ["email", "url", "domain", "ipv4", "ipv6", "mac_address",
                  "user_agent", "http", "uri", "port", "slug", "image_url", "hostname"]),
    ("address", ["address", "city", "street", "postcode", "zipcode", "country",
                 "state", "building", "latitude", "longitude", "postal"]),
    ("phone", ["phone", "msisdn"]),
    ("company", ["company", "bs", "catch_phrase"]),
    ("job", ["job"]),
    ("date_time", ["date", "time", "year", "month", "day", "century", "timezone", "am_pm"]),
    ("payment", ["credit_card", "iban", "swift", "currency", "bank", "pricetag"]),
    ("text", ["text", "sentence", "paragraph", "word"]),
    ("misc", ["uuid", "boolean", "md5", "sha1", "sha256", "password", "color",
              "file_", "mime_type", "emoji", "isbn", "license_plate", "vin"]),
]


def categorize(name: str) -> str:
    for category, keywords in CATEGORY_KEYWORDS:
        if any(k in name for k in keywords):
            return category
    return "other"


def get_providers(locale: str = "en_US") -> dict:
    """
    Introspects a Faker instance for the given locale and returns
    {category: [method_name, ...]} for every zero-argument-callable
    provider method -- i.e. every field type usable straight from the UI.
    """
    fake = Faker(locale)
    names = []
    for name in dir(fake):
        if name.startswith("_") or name in EXCLUDE:
            continue
        attr = getattr(fake, name, None)
        if not callable(attr):
            continue
        try:
            sig = inspect.signature(attr)
        except (ValueError, TypeError):
            continue
        required = [
            p for p in sig.parameters.values()
            if p.default is inspect.Parameter.empty
            and p.kind in (p.POSITIONAL_ONLY, p.POSITIONAL_OR_KEYWORD)
        ]
        if required:
            continue
        names.append(name)

    categories: dict[str, list[str]] = {}
    for name in sorted(set(names)):
        categories.setdefault(categorize(name), []).append(name)
    return dict(sorted(categories.items()))


def make_faker(locale: str = "en_US", seed=None) -> Faker:
    fake = Faker(locale)
    if seed is not None:
        Faker.seed(seed)
    return fake


def generate_one(fake: Faker, fields: list) -> dict:
    row = {}
    for f in fields:
        method = getattr(fake, f.get("provider", ""), None)
        if method is None or not callable(method):
            row[f["name"]] = None
            continue
        try:
            row[f["name"]] = method()
        except Exception as e:  # a malformed field shouldn't crash the batch
            row[f["name"]] = f"<error: {e}>"
    return row


def generate_rows(fields: list, rows: int, locale: str = "en_US", seed=None) -> list:
    fake = make_faker(locale, seed)
    return [generate_one(fake, fields) for _ in range(rows)]
