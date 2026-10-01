# Monitor pracy w Przemyślu — wszystkie oferty, bez selekcji „dla kobiety".
# Jeden warunek: miejsce pracy w Przemyślu / okolicach.
# Uruchomienie: python monitor/run.py → skan + index.html

CITY_OK = ("przemyśl", "przemy", "przemysl")

# ODRZUCENIA — tylko geografia: praca zdalna, za granicą, relokacja w inne miasto.
# zero selekcji zawodowej (nie ma „dla kobiety”, nie ma „bez biura”).
EXCLUDE = (
    # zdalna / hybrydowa
    "zdaln", "home office", "praca zdalna", "hybrydow", "remote", "praca w zdal",
    # za granicą / agencje zagraniczne
    "gmbh", "niemieckim", "niemieck", "arbeit", "ausland", "holland",
    "holandi", "niderland", "belgi", "niemczech", "czechy",
    "słowacj", "slowacj", "anglii", "wielkiej brytanii", "irlandi", "norwegi",
    "szwecji", "francji", "hiszpanii", "portugalii", "za granicą", "za granica",
    "wyjazd", "niemcy",
    "(de)", "-de)", "-de ", "(nl)", "-nl)", "(be)", "-be)", "(at)", "-at)",
    "(cz)", "-cz)", "(sk)", "-sk)", "(fr)", "-fr)", "(gb)", "-uk)",
    "hohenm", "zusmarsh", "cm-ft-de", "as-de",
)

# BIAŁA LISTA — wyłączona. Zostawiona jako dokumentacja, co kiedyś było odfiltrowywane.
# Włączenie (WHITELIST_ON = True) znów przepuści tylko stanowiska "typowo kobiece".
WHITELIST_ON = False
INCLUDE = (
    # sprzedaż / sklep / obsługa klienta
    "sprzedaz", "sprzedaż", "sprzedawc", "ekspedient", "kasjer", "kasjerka",
    "pracownik sklepu", "pracownik handlu", "wykładanie", "wykladanie",
    "obsługa klienta", "obsluga klienta", "obsługa kasy", "obsluga kasy",
    "doradca klienta", "doradczyni", "przyjmowanie towar", "inwentaryzacj",
    "handlow", "sklep", "salon", "stoisko", "kasa", "promotor", "ambasador",
    "hostess", "kierownik sklepu", "kierownik zmiany", "lider sklepu",
    # gastronomia / hotelarstwo / usługi
    "kelner", "kelnerka", "kucharz", "gastronom", "barman", "barista",
    "restauracj", "pizzeria", "kebab", "pomoc kuchenna", "pomoc kucharza",
    "zmywak", "piekarz", "cukiernik", "obsługa gości", "obsluga gosci",
    "obsługa bar", "obsluga bar", "obsluga stolika", "pomoc barmana",
    "pracownik kuchni", "pracownik restauracji", "hotel", "hotelarst",
    "pokojowa", "pokojowy", "recepcjonist", "housekeeping", "pralnia",
    "sprząt", "sprzat", "czystosc", "czystości", "utrzymania czystosci",
    # zdrowie / uroda / farmacja (obsługa fizyczna, nie biuro)
    "farmac", "magister farmacji", "technik farmacji", "aptek",
    "pielęgniar", "pielegniar", "opiekunk", "opiekun", "opiekunka",
    "opieka nad", "opiekun osób", "niani", "niania", "fizjoterapeut",
    "kosmetolog", "kosmetyczk", "fryzjer", "stylistk", "stylista",
    "paznokci", "makijaż", "makijaz", "masaż", "masaz", "uroda",
    "pielęgnacj", "pielegnacj", "pracownik medyczny",
    # lekka produkcja / magazyn / pakowanie
    "produkcj", "pakowacz", "pakowanie", "magazyn", "kompletacj", "komisjon",
    "sortowacz", "pracownik produkcji", "pracownik magazynu", "pracownik hali",
    "pracownik hali produkcyjnej", "pracownik firmy", "operator wtrysk",
    "operator linii", "operator cnc", "logistyk",
    # pozostałe lokalne / fizyczne / sezonowe
    "ogrodnik", "zbiór", "zbior", "sadzon", "kurier", "dostawca",
    "kontroler bilet", "dozorc", "portier", "windziarz", "pracownik ochrony",
    "pracownik fizyczny", "stażyst", "stazyst",
    "pracownica", "pracowniczka", "kobieta", "k/m", "m/k",
)

DB_PATH = "monitor/data/jobs.db"
HTML_OUT = "index.html"  # relativnie do root projektu

SOURCES = (
    "olx",
    "pracuj",
    "gowork",
    "egospodarka",
    "infopraca",
    "pracapl",
    "nuzle",
    "przemyslpraca",
    "ogloszeniaprz",
    "kariera",
    "rocketjobs",
    "manual",
)

PRACAPL_KEYWORDS = (
    "sprzedawca", "magazynier", "kasjer", "produkcja", "kierowca",
    "kelner", "kucharz", "operator", "pracownik-sklepu", "hala",
    "spawacz", "mechanik", "pomocnik", "praca-fizyczna",
)

RATE_LIMIT_S = 2.0
