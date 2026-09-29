# Monitor pracy w Przemyślu — oferta dla kobiety.
# Zero: biuro, budżetówka, państwówka, administracja, urzędy.
# Uruchomienie: python monitor/run.py → skan + index.html

CITY_OK = ("przemyśl", "przemy", "przemysl")

# TWARDE ODRZUCENIA — biuro / budżetówka / państwówka / administracja / za granicę
EXCLUDE = (
    # biuro i administracja
    "biurow", "administracj", "urzędnik", "urzednik", "referent", "sekretark",
    "asystent", "kadrow", "księgow", "ksiegow", "fakturzyst", "samorząd", "samorzad",
    "kadr ", "rekrutacj", "hr ", "płacowe", "placowe", "wynagrodzen",
    "biuro rachunk", "call center", "pracownik biura", "sprzedaz biurow",
    # urzędy / instytucje publiczne / budżetówka / państwówka
    "urząd", "urzad", "urzedu", "urzędzie", "starostw", "gminy ", "gminie ",
    "gminna ", "gminny", "ministerstw", "instytucja publiczn", "jednostka samorz",
    "urząd miasta", "urzedzie miasta", "wydzial", "wydziału",
    "szpital", "przychodni", "pogotow", "sanitarnepid", "sanitarno-epid",
    "państwow", "panstwow", "budzetowk", "budżetówk",
    "policj", "straż poż", "straz poz", "straż miejsk", "wojsk", "mundurow",
    "nauczyciel", "przedszkol", "szkoł", "szkol", "uczeln", "uniwersytet",
    "bibliotek", "muzeum", "teatr",
    "nfz", " zus", "zus ", "krus", "arimr", "inspektorat", "sąd ", "sad ",
    "prokuratur", "kancelari", "bank", "ubezpieczen",
    "mzk", "mpgk", "pwik", "zuk ", "poczta polsk", "pkp ",
    "spółk komunaln", "spolka komunaln", "komunaln",
    # zamówienia publiczne / urząd / inspektor biurowy
    "zamowien publicz", "zamówień publicz", "zamowienia publiczn",
    "inwestycji i zamowien", "inwestycji i zamówień", "uron",
    # analityka / IT / projektowe
    "analityk", "analityczk", "analyst", "data anal",
    "dzialu projektowego", "projektow",
    # biurowe sales / finanse / B2B
    "biznesow", "b2b", "finansow", "business development", "bdm",
    "nieruchomos",
    "miejscowosciach pols", "miejscowościach pols",
    # zdalne / hybrydowe biuro
    "zdaln", "home office", "praca zdalna", "hybrydow",
    "programist", "grafik ", "tester ", "software", "developer",
    # IT / korpo
    "data scien", "ux ", "product own", "project manag",
    # agencje zagraniczne / praca poza Polska
    "gmbh", "niemieckim", "niemieck", "arbeit", "ausland", "holland",
    "holandi", "niderland", "belgi", "niemczech", "czechy",
    "słowacj", "slowacj", "anglii", "wielkiej brytanii", "irlandi", "norwegi",
    "szwecji", "francji", "hiszpani", "portugalii", "za granicą", "za granica",
    "wyjazd", "niemcy",
    "(de)", "-de)", "-de ", "(nl)", "-nl)", "(be)", "-be)", "(at)", "-at)",
    "(cz)", "-cz)", "(sk)", "-sk)", "(fr)", "-fr)", "(gb)", "-uk)",
    "hohenm", "zusmarsh", "cm-ft-de", "as-de",
)

# BIAŁA LISTA — praca raczej dla kobiety (tytuł musi trafić w ≥1 słowo)
WHITELIST_ON = True
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
)

PRACAPL_KEYWORDS = (
    "sprzedawca", "magazynier", "kasjer", "produkcja", "kierowca",
    "kelner", "kucharz", "operator", "pracownik-sklepu", "hala",
    "spawacz", "mechanik", "pomocnik", "praca-fizyczna",
)

RATE_LIMIT_S = 2.0
