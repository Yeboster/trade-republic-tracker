"""
Merchant → Category mapping via keyword matching.

Add merchants here as you discover them. Case-insensitive matching.
"""

import logging
import unicodedata
import re
import csv
import os
from pathlib import Path

logger = logging.getLogger(__name__)

def normalize_text(text: str) -> str:
    """
    Normalizes text: lowercase, strip, remove accents,
    replace special chars with spaces.
    e.g. "Caffè @ Nero!" -> "caffe nero"
    """
    if not text:
        return ""
    
    # 1. Unicode normalization (NFD splits char + combining accent)
    text = unicodedata.normalize('NFD', text)
    
    # 2. Filter out non-spacing mark characters (accents)
    text = "".join(c for c in text if unicodedata.category(c) != 'Mn')
    
    # 3. Lowercase
    text = text.lower()
    
    # 4. Replace non-alphanumeric characters with spaces
    # Keep only a-z, 0-9 and spaces
    text = re.sub(r'[^a-z0-9\s]', ' ', text)
    
    # 5. Collapse multiple spaces and strip
    text = re.sub(r'\s+', ' ', text)
    
    return text.strip()

_csv_rules = []

def load_csv_rules():
    """Loads merchant → category rules from data/categories.csv if present."""
    global _csv_rules
    if _csv_rules:
        return

    # projects/trade-republic-tracker/src/tracker/categories.py -> .../data/categories.csv
    base_dir = Path(__file__).resolve().parent.parent.parent
    csv_path = base_dir / "data" / "categories.csv"
    
    if not csv_path.exists():
        logger.debug(f"No categories CSV found at {csv_path}")
        return

    try:
        count = 0
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            try:
                first_row = next(reader)
                if first_row and "Merchant" in first_row[0]:
                    pass # Header, skip
                else:
                    if len(first_row) >= 2:
                        merchant, category = first_row[0], first_row[1]
                        norm_merchant = normalize_text(merchant)
                        if norm_merchant and category:
                            _csv_rules.append((norm_merchant, category))
                            count += 1
            except StopIteration:
                pass

            for row in reader:
                if len(row) >= 2:
                    merchant, category = row[0], row[1]
                    norm_merchant = normalize_text(merchant)
                    if norm_merchant and category:
                        _csv_rules.append((norm_merchant, category))
                        count += 1
        
        # Sort rules by keyword length (longest first) to match specific rules before general ones
        # e.g. "uber eats" before "uber"
        _csv_rules.sort(key=lambda x: len(x[0]), reverse=True)
        
        logger.info(f"Loaded {count} rules from categories.csv")
    except Exception as e:
        logger.error(f"Failed to load categories CSV: {e}")


# Default built-in rules
# Keyword → category. First match wins.
# IMPORTANT: Keys should be normalized (lowercase, no accents)
MERCHANT_RULES = [
    ("cpam caisse primaire d assurance maladie", "Health"),
    ("empresa malaguena de transportes", "Shopping"),
    ("palais omnisports de paris bercy", "Entertainment"),
    ("centre dentaire ferney voltaire", "Health"),
    ("restaurants bouillon chartier", "Restaurant"),
    ("reunion des musees nationaux", "Entertainment"),
    ("metropole rouen normandie", "Transport"),
    ("pharmaciedesteinfort24241", "Health"),
    ("aparcament de l esgl sia", "Transport"),
    ("aparcament prada casadet", "Transport"),
    ("bellavista bar ristorant", "Restaurant"),
    ("museo cappella sansevero", "Entertainment"),
    ("orygyns specialty coffee", "Café"),
    ("paypal ami4883x shoppy m", "Services"),
    ("paypal nohamalik99 shopp", "Services"),
    ("paypal tenore emanuele00", "Services"),
    ("rizzato calzature megast", "Transport"),
    ("royaltea ba mlynske nivy", "Café"),
    ("tabak press oc eurovea 2", "Shopping"),
    ("yann couvreur patisserie", "Restaurant"),
    ("autostrade per l italia", "Transport"),
    ("caffe al morar di roman", "Café"),
    ("caffetteria della nonna", "Café"),
    ("la tete dans les nuages", "Entertainment"),
    ("little by cipolla caffe", "Café"),
    ("museo picasso t distrib", "Entertainment"),
    ("nyx sncfgaresetconnexio", "Transport"),
    ("sumup associazione la v", "Services"),
    ("sumup burger theory lev", "Restaurant"),
    ("superstrada pedemontana", "Transport"),
    ("ls da lino epicerie mu", "Grocery"),
    ("perfect hair health me", "Services"),
    ("pro ski martinske hole", "Entertainment"),
    ("ufficio cultura teatro", "Restaurant"),
    ("gelateria ice town di", "Restaurant"),
    ("il postto gelato cafe", "Café"),
    ("karasardegna landside", "Transport"),
    ("sp narodna zoo bojnic", "Entertainment"),
    ("sumup dr sayous paris", "Services"),
    ("tunels barcelona cadi", "Transport"),
    ("borabora bufet pizza", "Restaurant"),
    ("parkov centr bojnice", "Transport"),
    ("pro ski obcerstvenie", "Entertainment"),
    ("trattoria sabbioneda", "Restaurant"),
    ("bistro de la balise", "Restaurant"),
    ("klarna google store", "Subscription"),
    ("notre dame de paris", "Entertainment"),
    ("ospedale parcheggio", "Transport"),
    ("paypal mihaicip1982", "Services"),
    ("pharmacie du marais", "Health"),
    ("phmcie vieux marche", "Grocery"),
    ("trade republic card", "Restaurant"),
    ("bar a bulles paris", "Restaurant"),
    ("bar merc atarazana", "Restaurant"),
    ("bufet dkz gastro s", "Transport"),
    ("ffaxcopy94 ba nivy", "Services"),
    ("food senza glutine", "Restaurant"),
    ("galeries lafayette", "Shopping"),
    ("gelateria i nobili", "Restaurant"),
    ("lipscani souvenirs", "Shopping"),
    ("malaga stop hostel", "Travel"),
    ("mediterranean food", "Restaurant"),
    ("pagnol boulangerie", "Grocery"),
    ("paypal afritithamz", "Services"),
    ("paypal erik covolo", "Services"),
    ("paypal lexdavies19", "Services"),
    ("pharmacie secretan", "Health"),
    ("r114 briccocafe ai", "Café"),
    ("s v t autostazione", "Transport"),
    ("aparcament vinyes", "Transport"),
    ("arena padel s s d", "Entertainment"),
    ("carrefour express", "Grocery"),
    ("climbing district", "Entertainment"),
    ("crai supermercati", "Grocery"),
    ("la cabane a mario", "Transport"),
    ("laverie lav speed", "Services"),
    ("le popup du label", "Health"),
    ("librerias picasso", "Shopping"),
    ("marano cinema srl", "Entertainment"),
    ("paypal locservice", "Services"),
    ("sumup emma crepes", "Restaurant"),
    ("bowling time snc", "Entertainment"),
    ("carollo riccardo", "Transport"),
    ("carrefour market", "Grocery"),
    ("curiosity stream", "Subscription"),
    ("docteur montloin", "Health"),
    ("grande pharmacie", "Health"),
    ("hotel etats unis", "Travel"),
    ("ipp park hrad ba", "Entertainment"),
    ("malpensa shuttle", "Transport"),
    ("noir coffee shop", "Café"),
    ("osteria al volto", "Restaurant"),
    ("restauracia five", "Restaurant"),
    ("sas sdg fleur 38", "Shopping"),
    ("supermarches g20", "Grocery"),
    ("trattoria du val", "Restaurant"),
    ("val se de crepes", "Restaurant"),
    ("vasa lekaren elf", "Shopping"),
    ("aparcaments bsm", "Transport"),
    ("billetterie mja", "Entertainment"),
    ("class souvenirs", "Shopping"),
    ("dermatologie bi", "Health"),
    ("el corte ingles", "Shopping"),
    ("fatra ski s r o", "Entertainment"),
    ("parafarmacia it", "Shopping"),
    ("subarashi ramen", "Restaurant"),
    ("fnac spectacle", "Entertainment"),
    ("cafe du temple", "Café"),
    ("carrefour city", "Grocery"),
    ("climbing genie", "Entertainment"),
    ("google storage", "Subscription"),
    ("hotel 1k paris", "Travel"),
    ("lastminute com", "Transport"),
    ("paname brewing", "Restaurant"),
    ("paris baguette", "Restaurant"),
    ("passetonbillet", "Entertainment"),
    ("paypal papmpol", "Services"),
    ("sc canal sushi", "Restaurant"),
    ("sp xtremeskins", "Entertainment"),
    ("terres de cafe", "Café"),
    ("thermalpark ds", "Entertainment"),
    ("thermalpark sk", "Entertainment"),
    ("brioche doree", "Restaurant"),
    ("discover cars", "Transport"),
    ("fresco market", "Grocery"),
    ("google chrome", "Subscription"),
    ("google wallet", "Subscription"),
    ("jdp librairie", "Transport"),
    ("juice factory", "Café"),
    ("la seine cafe", "Café"),
    ("lafeltrinelli", "Shopping"),
    ("lowrider cafe", "Café"),
    ("new soul food", "Restaurant"),
    ("paypal sultan", "Services"),
    ("pret a manger", "Restaurant"),
    ("the cambridge", "Transport"),
    ("tune my music", "Subscription"),
    ("leroy merlin", "Shopping"),
    ("amazon prime", "Shopping"),
    ("ticketmaster", "Entertainment"),
    ("axa schengen", "Services"),
    ("bar da kalif", "Restaurant"),
    ("blitzsociety", "Entertainment"),
    ("cerballiance", "Health"),
    ("google cloud", "Subscription"),
    ("google store", "Subscription"),
    ("mammy gateau", "Café"),
    ("pam panorama", "Grocery"),
    ("regal burger", "Restaurant"),
    ("slovak lines", "Transport"),
    ("sumup begona", "Services"),
    ("sushi maison", "Restaurant"),
    ("intermarche", "Grocery"),
    ("grand frais", "Grocery"),
    ("boulangerie", "Grocery"),
    ("burger king", "Restaurant"),
    ("total energ", "Transport"),
    ("free mobile", "Utilities"),
    ("booking com", "Travel"),
    ("bricco cafe", "Café"),
    ("buffet gare", "Restaurant"),
    ("cafe bogota", "Café"),
    ("coccimarket", "Grocery"),
    ("dm drogerie", "Shopping"),
    ("fubin sushi", "Restaurant"),
    ("google play", "Subscription"),
    ("holiday bar", "Travel"),
    ("little cafe", "Café"),
    ("manawa poke", "Restaurant"),
    ("napoli cafe", "Café"),
    ("pro ski a s", "Entertainment"),
    ("rougier ple", "Shopping"),
    ("see tickets", "Entertainment"),
    ("thermalpark", "Entertainment"),
    ("wanted cafe", "Café"),
    ("restaurant", "Restaurant"),
    ("aliexpress", "Shopping"),
    ("air france", "Travel"),
    ("aerobus co", "Transport"),
    ("amazon pay", "Shopping"),
    ("aroma zone", "Shopping"),
    ("citypharma", "Shopping"),
    ("cloudflare", "Subscription"),
    ("emcard com", "Transport"),
    ("eventbrite", "Entertainment"),
    ("google one", "Subscription"),
    ("maxicoffee", "Café"),
    ("mcdonald s", "Restaurant"),
    ("midaticket", "Entertainment"),
    ("new yorker", "Shopping"),
    ("park guell", "Entertainment"),
    ("pizza wawa", "Restaurant"),
    ("sq bcoffee", "Café"),
    ("supersonic", "Entertainment"),
    ("the museum", "Entertainment"),
    ("trenitalia", "Transport"),
    ("carrefour", "Grocery"),
    ("bio c bon", "Grocery"),
    ("naturalia", "Grocery"),
    ("boucherie", "Grocery"),
    ("uber eats", "Food Delivery"),
    ("deliveroo", "Food Delivery"),
    ("starbucks", "Café"),
    ("brasserie", "Restaurant"),
    ("blablacar", "Transport"),
    ("decathlon", "Shopping"),
    ("boulanger", "Shopping"),
    ("apple.com", "Subscription"),
    ("pharmacie", "Health"),
    ("transavia", "Travel"),
    ("agrifarma", "Shopping"),
    ("aquardens", "Entertainment"),
    ("autogrill", "Transport"),
    ("billetweb", "Entertainment"),
    ("bitwarden", "Subscription"),
    ("budgetair", "Transport"),
    ("e leclerc", "Grocery"),
    ("fun party", "Entertainment"),
    ("montyesim", "Subscription"),
    ("namecheap", "Subscription"),
    ("potraviny", "Grocery"),
    ("trainline", "Travel"),
    ("treatwell", "Services"),
    ("u express", "Grocery"),
    ("weezevent", "Entertainment"),
    ("westfield", "Shopping"),
    ("monoprix", "Grocery"),
    ("franprix", "Grocery"),
    ("epicerie", "Grocery"),
    ("just eat", "Food Delivery"),
    ("mcdonald", "Restaurant"),
    ("traiteur", "Restaurant"),
    ("pharmacy", "Health"),
    ("doctolib", "Health"),
    ("dentaire", "Health"),
    ("bouygues", "Utilities"),
    ("datacamp", "Subscription"),
    ("emisfero", "Grocery"),
    ("farmacia", "Shopping"),
    ("kaufland", "Grocery"),
    ("la poste", "Services"),
    ("marche u", "Grocery"),
    ("musee ja", "Entertainment"),
    ("ovhcloud", "Subscription"),
    ("reserved", "Shopping"),
    ("uber one", "Transport"),
    ("withings", "Shopping"),
    ("leclerc", "Grocery"),
    ("super u", "Grocery"),
    ("primeur", "Grocery"),
    ("station", "Transport"),
    ("parking", "Transport"),
    ("autolib", "Transport"),
    ("primark", "Shopping"),
    ("netflix", "Subscription"),
    ("spotify", "Subscription"),
    ("youtube", "Subscription"),
    ("chatgpt", "Subscription"),
    ("optique", "Health"),
    ("medecin", "Health"),
    ("booking", "Travel"),
    ("ryanair", "Travel"),
    ("easyjet", "Travel"),
    ("flixbus", "Travel"),
    ("cafe co", "Café"),
    ("copains", "Grocery"),
    ("dice fm", "Entertainment"),
    ("dynadot", "Subscription"),
    ("eurovea", "Shopping"),
    ("godaddy", "Subscription"),
    ("planity", "Services"),
    ("revolut", "Services"),
    ("telekom", "Utilities"),
    ("zalando", "Shopping"),
    ("zooplus", "Entertainment"),
    ("auchan", "Grocery"),
    ("picard", "Grocery"),
    ("casino", "Grocery"),
    ("marche", "Grocery"),
    ("domino", "Restaurant"),
    ("bistro", "Restaurant"),
    ("navigo", "Transport"),
    ("amazon", "Shopping"),
    ("uniqlo", "Shopping"),
    ("action", "Shopping"),
    ("disney", "Subscription"),
    ("google", "Subscription"),
    ("notion", "Subscription"),
    ("openai", "Subscription"),
    ("github", "Subscription"),
    ("icloud", "Subscription"),
    ("orange", "Utilities"),
    ("cinema", "Entertainment"),
    ("airbnb", "Travel"),
    ("hostel", "Travel"),
    ("autema", "Transport"),
    ("despar", "Grocery"),
    ("miniso", "Shopping"),
    ("mytrip", "Transport"),
    ("normal", "Shopping"),
    ("notino", "Shopping"),
    ("paypal", "Services"),
    ("scribd", "Subscription"),
    ("subway", "Restaurant"),
    ("therme", "Entertainment"),
    ("vinted", "Shopping"),
    ("xiaomi", "Shopping"),
    ("sushi", "Restaurant"),
    ("pizza", "Restaurant"),
    ("kebab", "Restaurant"),
    ("shell", "Transport"),
    ("darty", "Shopping"),
    ("shein", "Shopping"),
    ("apple", "Shopping"),
    ("adobe", "Subscription"),
    ("engie", "Utilities"),
    ("pathe", "Entertainment"),
    ("hotel", "Travel"),
    ("train", "Travel"),
    ("aumai", "Shopping"),
    ("billa", "Grocery"),
    ("brave", "Restaurant"),
    ("celio", "Shopping"),
    ("cropp", "Shopping"),
    ("druni", "Shopping"),
    ("fedex", "Services"),
    ("renfe", "Transport"),
    ("skeat", "Restaurant"),
    ("swile", "Services"),
    ("velib", "Transport"),
    ("lidl", "Grocery"),
    ("aldi", "Grocery"),
    ("cafe", "Café"),
    ("sncf", "Transport"),
    ("ratp", "Transport"),
    ("uber", "Transport"),
    ("bolt", "Transport"),
    ("esso", "Transport"),
    ("lime", "Transport"),
    ("tier", "Transport"),
    ("fnac", "Shopping"),
    ("zara", "Shopping"),
    ("ikea", "Shopping"),
    ("kine", "Health"),
    ("bunq", "Restaurant"),
    ("coop", "Grocery"),
    ("hema", "Shopping"),
    ("livi", "Health"),
    ("temu", "Shopping"),
    ("kfc", "Restaurant"),
    ("bp ", "Transport"),
    ("voi", "Transport"),
    ("h&m", "Shopping"),
    ("edf", "Utilities"),
    ("sfr", "Utilities"),
    ("ugc", "Entertainment"),
    ("aws", "Subscription"),
    ("axa", "Services"),
    ("obb", "Transport"),
    ("omv", "Transport"),
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
    Checks CSV rules first, then runtime rules, then built-in defaults.
    """
    if not merchant_name:
        return "Other"
    
    load_csv_rules()
    
    # Normalize input: lowercase, remove accents
    norm_name = normalize_text(merchant_name)

    # Check CSV rules
    for keyword, category in _csv_rules:
        if keyword in norm_name:
            return category
    
    # Check runtime (custom) rules first
    for keyword, category in _runtime_rules:
        if keyword in norm_name:
            return category
            
    # Check defaults
    for keyword, category in MERCHANT_RULES:
        if keyword in norm_name:
            return category
    
    return "Other"


def append_rules_to_csv(rules: list) -> int:
    """
    Appends new merchant → category rules to data/categories.csv.
    
    Args:
        rules: List of dicts with 'merchant' and 'category' keys
    
    Returns:
        Number of rules added
    """
    global _csv_rules
    
    base_dir = Path(__file__).resolve().parent.parent.parent
    csv_path = base_dir / "data" / "categories.csv"
    
    # Create data directory if needed
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Check if file exists (need header)
    file_exists = csv_path.exists()
    
    # Load existing rules to avoid duplicates
    load_csv_rules()
    existing_merchants = {normalize_text(r[0]) for r in _csv_rules}
    
    # Filter out duplicates
    new_rules = []
    for rule in rules:
        merchant = rule.get('merchant', '')
        category = rule.get('category', '')
        if not merchant or not category:
            continue
        norm_merchant = normalize_text(merchant)
        if norm_merchant not in existing_merchants:
            new_rules.append((merchant, category))
            existing_merchants.add(norm_merchant)
    
    if not new_rules:
        return 0
    
    try:
        with open(csv_path, 'a', encoding='utf-8', newline='') as f:
            writer = csv.writer(f)
            
            # Write header if new file
            if not file_exists:
                writer.writerow(["Merchant", "Category"])
            
            for merchant, category in new_rules:
                writer.writerow([merchant, category])
        
        # Reload rules to include newly added ones
        _csv_rules.clear()
        load_csv_rules()
        
        logger.info(f"Added {len(new_rules)} rules to categories.csv")
        return len(new_rules)
        
    except Exception as e:
        logger.error(f"Failed to append rules to CSV: {e}")
        return 0
