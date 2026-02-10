"""
Merchant → Category mapping via keyword matching.

Add merchants here as you discover them. Case-insensitive matching.
"""

import logging
import unicodedata

logger = logging.getLogger(__name__)

def normalize_text(text: str) -> str:
    """
    Normalizes text: lowercase, strip, remove accents.
    e.g. "Caffè Nero" -> "caffe nero"
    """
    if not text:
        return ""
    
    # Unicode normalization (NFD splits char + combining accent)
    text = unicodedata.normalize('NFD', text)
    # Filter out non-spacing mark characters (accents)
    text = "".join(c for c in text if unicodedata.category(c) != 'Mn')
    
    return text.lower().strip()


# Default built-in rules
# Keyword → category. First match wins.
# IMPORTANT: Keys should be normalized (lowercase, no accents)
MERCHANT_RULES = [
    # ── Grocery ──────────────────────────────
    ("monoprix", "Grocery"),
    ("carrefour", "Grocery"),
    ("auchan", "Grocery"),
    ("leclerc", "Grocery"),
    ("lidl", "Grocery"),
    ("aldi", "Grocery"),
    ("intermarche", "Grocery"),  # covers intermarché
    ("franprix", "Grocery"),
    ("picard", "Grocery"),
    ("casino", "Grocery"),
    ("super u", "Grocery"),
    ("bio c bon", "Grocery"),
    ("naturalia", "Grocery"),
    ("grand frais", "Grocery"),
    ("marche", "Grocery"),      # covers marché
    ("primeur", "Grocery"),
    ("boucherie", "Grocery"),
    ("boulangerie", "Grocery"),
    ("epicerie", "Grocery"),    # covers épicerie

    # ── Restaurants & Food ───────────────────
    ("uber eats", "Food Delivery"),
    ("deliveroo", "Food Delivery"),
    ("just eat", "Food Delivery"),
    ("mcdonald", "Restaurant"),
    ("burger king", "Restaurant"),
    ("kfc", "Restaurant"),
    ("domino", "Restaurant"),
    ("starbucks", "Café"),
    ("cafe", "Café"),           # covers café, caffé
    ("restaurant", "Restaurant"),
    ("brasserie", "Restaurant"),
    ("sushi", "Restaurant"),
    ("pizza", "Restaurant"),
    ("kebab", "Restaurant"),
    ("bistro", "Restaurant"),
    ("traiteur", "Restaurant"),

    # ── Transport ────────────────────────────
    ("sncf", "Transport"),
    ("ratp", "Transport"),
    ("uber", "Transport"),  # after uber eats
    ("bolt", "Transport"),
    ("blablacar", "Transport"),
    ("navigo", "Transport"),
    ("total energ", "Transport"),
    ("shell", "Transport"),
    ("bp ", "Transport"),
    ("esso", "Transport"),
    ("station", "Transport"),
    ("parking", "Transport"),
    ("autolib", "Transport"),
    ("lime", "Transport"),
    ("tier", "Transport"),
    ("voi", "Transport"),

    # ── Shopping ─────────────────────────────
    ("amazon", "Shopping"),
    ("fnac", "Shopping"),
    ("darty", "Shopping"),
    ("decathlon", "Shopping"),
    ("zara", "Shopping"),
    ("h&m", "Shopping"),
    ("uniqlo", "Shopping"),
    ("ikea", "Shopping"),
    ("leroy merlin", "Shopping"),
    ("action", "Shopping"),
    ("primark", "Shopping"),
    ("aliexpress", "Shopping"),
    ("shein", "Shopping"),
    ("apple", "Shopping"),
    ("boulanger", "Shopping"),

    # ── Subscriptions ────────────────────────
    ("netflix", "Subscription"),
    ("spotify", "Subscription"),
    ("disney", "Subscription"),
    ("apple.com", "Subscription"),
    ("google", "Subscription"),
    ("youtube", "Subscription"),
    ("amazon prime", "Subscription"),
    ("notion", "Subscription"),
    ("openai", "Subscription"),
    ("chatgpt", "Subscription"),
    ("github", "Subscription"),
    ("icloud", "Subscription"),
    ("adobe", "Subscription"),

    # ── Health & Pharmacy ────────────────────
    ("pharmacie", "Health"),
    ("pharmacy", "Health"),
    ("doctolib", "Health"),
    ("optique", "Health"),
    ("dentaire", "Health"),
    ("medecin", "Health"),      # covers médecin
    ("kine", "Health"),         # covers kiné

    # ── Bills & Utilities ────────────────────
    ("edf", "Utilities"),
    ("engie", "Utilities"),
    ("free mobile", "Utilities"),
    ("orange", "Utilities"),
    ("sfr", "Utilities"),
    ("bouygues", "Utilities"),

    # ── Entertainment ────────────────────────
    ("cinema", "Entertainment"), # covers cinéma
    ("ugc", "Entertainment"),
    ("pathe", "Entertainment"),  # covers pathé
    ("fnac spectacle", "Entertainment"),
    ("ticketmaster", "Entertainment"),

    # ── Travel ───────────────────────────────
    ("airbnb", "Travel"),
    ("booking", "Travel"),
    ("hotel", "Travel"),
    ("hostel", "Travel"),
    ("ryanair", "Travel"),
    ("easyjet", "Travel"),
    ("air france", "Travel"),
    ("transavia", "Travel"),
    ("flixbus", "Travel"),
    ("train", "Travel"),
]

# Can be extended at runtime
_runtime_rules = []

def add_rule(merchant_keyword: str, category: str):
    """Adds a custom rule at runtime (inserted at the top)."""
    norm_keyword = normalize_text(merchant_keyword)
    _runtime_rules.insert(0, (norm_keyword, category))

def categorize_merchant(merchant_name: str) -> str:
    """
    Returns a spending category for a merchant name.
    Checks runtime rules first, then built-in defaults.
    """
    if not merchant_name:
        return "Other"
    
    # Normalize input: lowercase, remove accents
    norm_name = normalize_text(merchant_name)
    
    # Check runtime (custom) rules first
    for keyword, category in _runtime_rules:
        if keyword in norm_name:
            return category
            
    # Check defaults
    for keyword, category in MERCHANT_RULES:
        if keyword in norm_name:
            return category
    
    return "Other"
