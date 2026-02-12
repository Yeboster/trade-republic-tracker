"""
Merchant Name Normalization (Iteration 19)

Cleans up messy merchant names from card transactions:
- Removes store numbers/IDs (e.g., "LIDL #12345" → "LIDL")
- Removes trailing city/location suffixes
- Normalizes common brand names
- Handles truncated names from payment processors
"""
import re
from typing import Optional, Dict

# Known brand name mappings (messy → clean)
BRAND_MAPPINGS = {
    # Supermarkets
    "lidl": "Lidl",
    "aldi": "Aldi",
    "carrefour": "Carrefour",
    "auchan": "Auchan",
    "intermarche": "Intermarché",
    "leclerc": "Leclerc",
    "monoprix": "Monoprix",
    "franprix": "Franprix",
    "picard": "Picard",
    "casino": "Casino",
    "u express": "U Express",
    "super u": "Super U",
    "hyper u": "Hyper U",
    "biocoop": "Biocoop",
    "naturalia": "Naturalia",
    
    # Fast Food / Restaurants
    "mcdonald": "McDonald's",
    "mcdonalds": "McDonald's",
    "mcdonald's": "McDonald's",
    "burger king": "Burger King",
    "kfc": "KFC",
    "subway": "Subway",
    "starbucks": "Starbucks",
    "paul": "Paul",
    "pret a manger": "Pret A Manger",
    "five guys": "Five Guys",
    "domino": "Domino's",
    "dominos": "Domino's",
    "pizza hut": "Pizza Hut",
    
    # Transport
    "uber": "Uber",
    "uber eats": "Uber Eats",
    "ubereats": "Uber Eats",
    "bolt": "Bolt",
    "lyft": "Lyft",
    "blablacar": "BlaBlaCar",
    "freenow": "FREE NOW",
    "free now": "FREE NOW",
    "lime": "Lime",
    "tier": "Tier",
    "bird": "Bird",
    "voi": "Voi",
    "sncf": "SNCF",
    "ratp": "RATP",
    "navigo": "Navigo",
    "velib": "Vélib'",
    "autolib": "Autolib",
    "total": "Total",
    "shell": "Shell",
    "bp": "BP",
    "esso": "Esso",
    "elan": "Élan",
    
    # Tech / Subscriptions
    "amazon": "Amazon",
    "amazon prime": "Amazon Prime",
    "netflix": "Netflix",
    "spotify": "Spotify",
    "apple": "Apple",
    "google": "Google",
    "microsoft": "Microsoft",
    "paypal": "PayPal",
    "steam": "Steam",
    "playstation": "PlayStation",
    "xbox": "Xbox",
    "nintendo": "Nintendo",
    "adobe": "Adobe",
    "dropbox": "Dropbox",
    "notion": "Notion",
    "github": "GitHub",
    "openai": "OpenAI",
    "chatgpt": "ChatGPT",
    "anthropic": "Anthropic",
    "aws": "AWS",
    "digitalocean": "DigitalOcean",
    "hetzner": "Hetzner",
    "ovh": "OVH",
    "cloudflare": "Cloudflare",
    
    # Shopping
    "ikea": "IKEA",
    "decathlon": "Decathlon",
    "fnac": "Fnac",
    "darty": "Darty",
    "boulanger": "Boulanger",
    "leroy merlin": "Leroy Merlin",
    "castorama": "Castorama",
    "action": "Action",
    "primark": "Primark",
    "zara": "Zara",
    "h&m": "H&M",
    "uniqlo": "Uniqlo",
    "celio": "Celio",
    "jules": "Jules",
    "kiabi": "Kiabi",
    "aliexpress": "AliExpress",
    "ali express": "AliExpress",
    "wish": "Wish",
    "shein": "Shein",
    "temu": "Temu",
    "zalando": "Zalando",
    "asos": "ASOS",
    
    # Pharmacy / Health
    "pharmacie": "Pharmacie",
    "parapharmacie": "Parapharmacie",
    "doctolib": "Doctolib",
    
    # Banks / Finance
    "trade republic": "Trade Republic",
    "n26": "N26",
    "revolut": "Revolut",
    "wise": "Wise",
    "boursorama": "Boursorama",
    "ing": "ING",
    
    # Entertainment
    "cinema": "Cinéma",
    "ugc": "UGC",
    "pathe": "Pathé",
    "gaumont": "Gaumont",
    "mk2": "MK2",
    "grand rex": "Grand Rex",
}

# Patterns to strip from merchant names
STRIP_PATTERNS = [
    # Store numbers and IDs
    r'\s*#\d+$',           # "STORE #12345"
    r'\s*\*\d+$',          # "STORE *12345"
    r'\s+\d{4,}$',         # "STORE 123456"
    r'\s+s\.?r\.?l\.?$',   # "COMPANY SRL"
    r'\s+s\.?a\.?s\.?$',   # "COMPANY SAS"
    r'\s+s\.?a\.?$',       # "COMPANY SA"
    r'\s+gmbh$',           # "COMPANY GMBH"
    r'\s+ltd\.?$',         # "COMPANY LTD"
    r'\s+inc\.?$',         # "COMPANY INC"
    r'\s+co\.?$',          # "COMPANY CO"
    
    # Location suffixes (common patterns)
    r'\s+paris\s*\d*$',
    r'\s+lyon\s*\d*$',
    r'\s+marseille\s*\d*$',
    r'\s+bordeaux\s*\d*$',
    r'\s+toulouse\s*\d*$',
    r'\s+nantes\s*\d*$',
    r'\s+strasbourg\s*\d*$',
    r'\s+lille\s*\d*$',
    r'\s+nice\s*\d*$',
    r'\s+berlin\s*\d*$',
    r'\s+munich\s*\d*$',
    r'\s+münchen\s*\d*$',
    r'\s+frankfurt\s*\d*$',
    r'\s+hamburg\s*\d*$',
    
    # Terminal/transaction codes
    r'\s+[A-Z]{2,3}\d{3,}$',  # "STORE DE123456"
    r'\s+\d{2,4}[A-Z]{2,}$',  # "STORE 123AB"
    
    # Dates in names
    r'\s+\d{2}/\d{2}$',       # "STORE 12/25"
    r'\s+\d{2}\.\d{2}$',      # "STORE 12.25"
]

# Compile patterns for efficiency
_compiled_patterns = [re.compile(p, re.IGNORECASE) for p in STRIP_PATTERNS]


def normalize_merchant(name: str, use_mappings: bool = True) -> str:
    """
    Normalize a merchant name for cleaner display and better categorization.
    
    Args:
        name: Raw merchant name from transaction
        use_mappings: Whether to apply known brand mappings
        
    Returns:
        Cleaned merchant name
    """
    if not name:
        return "Unknown"
    
    # Start with basic cleanup
    cleaned = name.strip()
    
    # Strip patterns (store numbers, location suffixes, etc.)
    for pattern in _compiled_patterns:
        cleaned = pattern.sub('', cleaned).strip()
    
    # Remove excessive whitespace
    cleaned = ' '.join(cleaned.split())
    
    # Apply brand mappings if enabled
    if use_mappings:
        lower = cleaned.lower()
        
        # Exact match first
        if lower in BRAND_MAPPINGS:
            return BRAND_MAPPINGS[lower]
        
        # Prefix match (e.g., "mcdonald's paris" → "McDonald's")
        for key, brand in BRAND_MAPPINGS.items():
            if lower.startswith(key):
                return brand
    
    # Title case if all lowercase or all uppercase
    if cleaned.islower() or cleaned.isupper():
        # Smart title case (preserve some patterns)
        cleaned = smart_title_case(cleaned)
    
    return cleaned if cleaned else "Unknown"


def smart_title_case(s: str) -> str:
    """
    Title case with awareness of common patterns.
    """
    # Words to keep lowercase (unless first word)
    lowercase_words = {'de', 'du', 'des', 'le', 'la', 'les', 'et', 'the', 'a', 'an', 'of', 'in', 'on', 'at'}
    
    words = s.lower().split()
    result = []
    
    for i, word in enumerate(words):
        if i == 0:
            result.append(word.capitalize())
        elif word in lowercase_words:
            result.append(word)
        else:
            result.append(word.capitalize())
    
    return ' '.join(result)


def get_merchant_group(name: str) -> str:
    """
    Get the normalized group key for a merchant (for aggregation).
    
    This is more aggressive than display normalization - it groups
    variations of the same merchant together.
    
    Example: "Carrefour City Paris 7e" and "CARREFOUR EXPRESS" → "carrefour"
    """
    normalized = normalize_merchant(name, use_mappings=False).lower()
    
    # Check if it matches any known brand
    for key in BRAND_MAPPINGS.keys():
        if key in normalized or normalized.startswith(key.split()[0]):
            return key
    
    # Return first word as group key (often the brand)
    words = normalized.split()
    if words:
        return words[0]
    return "unknown"


class MerchantNormalizer:
    """
    Stateful merchant normalizer with custom mappings and learning.
    """
    
    def __init__(self, custom_mappings: Optional[Dict[str, str]] = None):
        """
        Args:
            custom_mappings: Additional raw→clean mappings to override defaults
        """
        self.custom_mappings = custom_mappings or {}
        self._cache: Dict[str, str] = {}
    
    def normalize(self, name: str) -> str:
        """Normalize with caching and custom mappings."""
        if name in self._cache:
            return self._cache[name]
        
        # Check custom mappings first (exact match)
        lower = name.lower().strip()
        if lower in self.custom_mappings:
            result = self.custom_mappings[lower]
        else:
            result = normalize_merchant(name)
        
        self._cache[name] = result
        return result
    
    def add_mapping(self, raw: str, clean: str) -> None:
        """Add a custom mapping."""
        self.custom_mappings[raw.lower().strip()] = clean
        # Invalidate cache for this key
        if raw in self._cache:
            del self._cache[raw]
    
    def get_suggestions(self, names: list) -> Dict[str, str]:
        """
        Suggest normalizations for a list of merchant names.
        
        Returns dict of raw → suggested clean name.
        """
        suggestions = {}
        for name in names:
            normalized = self.normalize(name)
            if normalized != name:
                suggestions[name] = normalized
        return suggestions
