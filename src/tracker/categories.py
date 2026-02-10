"""
Merchant → Category mapping via keyword matching.

Add merchants here as you discover them. Case-insensitive matching.
"""

# Keyword → category. First match wins, so order matters for ambiguous names.
# Keys are lowercased substrings to match against merchant name.
MERCHANT_RULES = [
    # ── Grocery ──────────────────────────────
    ("monoprix", "Grocery"),
    ("carrefour", "Grocery"),
    ("auchan", "Grocery"),
    ("leclerc", "Grocery"),
    ("lidl", "Grocery"),
    ("aldi", "Grocery"),
    ("intermarché", "Grocery"),
    ("intermarche", "Grocery"),
    ("franprix", "Grocery"),
    ("picard", "Grocery"),
    ("casino", "Grocery"),
    ("super u", "Grocery"),
    ("bio c bon", "Grocery"),
    ("naturalia", "Grocery"),
    ("grand frais", "Grocery"),
    ("marché", "Grocery"),
    ("marche", "Grocery"),
    ("primeur", "Grocery"),
    ("boucherie", "Grocery"),
    ("boulangerie", "Grocery"),
    ("épicerie", "Grocery"),
    ("epicerie", "Grocery"),

    # ── Restaurants & Food ───────────────────
    ("uber eats", "Food Delivery"),
    ("deliveroo", "Food Delivery"),
    ("just eat", "Food Delivery"),
    ("mcdonald", "Restaurant"),
    ("burger king", "Restaurant"),
    ("kfc", "Restaurant"),
    ("domino", "Restaurant"),
    ("starbucks", "Café"),
    ("café", "Café"),
    ("cafe", "Café"),
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
    ("médecin", "Health"),
    ("kiné", "Health"),

    # ── Bills & Utilities ────────────────────
    ("edf", "Utilities"),
    ("engie", "Utilities"),
    ("free mobile", "Utilities"),
    ("orange", "Utilities"),
    ("sfr", "Utilities"),
    ("bouygues", "Utilities"),

    # ── Entertainment ────────────────────────
    ("cinema", "Entertainment"),
    ("cinéma", "Entertainment"),
    ("ugc", "Entertainment"),
    ("pathé", "Entertainment"),
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
]


def categorize_merchant(merchant_name: str) -> str:
    """
    Returns a spending category for a merchant name.
    Falls back to 'Other' if no rule matches.
    """
    if not merchant_name:
        return "Other"
    
    name_lower = merchant_name.lower()
    
    for keyword, category in MERCHANT_RULES:
        if keyword in name_lower:
            return category
    
    return "Other"
