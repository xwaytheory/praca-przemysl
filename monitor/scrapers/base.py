"""Wspolne parsowanie + rejestrowanie scraperow."""
import hashlib
import html as htmllib
import re
from datetime import date, timedelta

REGISTRY: dict[str, callable] = {}


def register(name):
    def deco(fn):
        REGISTRY[name] = fn
        return fn

    return deco


def clean(s: str | None) -> str:
    s = htmllib.unescape(s or "")
    s = re.sub(r"\s+", " ", s)
    return s.strip()


def h_id(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]


SALARY_RE = re.compile(r"(\d[\d\s.,]{2,})\s*(?:zł|PLN)", re.I)


def salary_from(*texts: str) -> str:
    for t in texts:
        m = SALARY_RE.search(t or "")
        if m:
            return clean(m.group(0))
    return ""


MONTHS = {
    "stycznia": 1, "lutego": 2, "marca": 3, "kwietnia": 4, "maja": 5,
    "czerwca": 6, "lipca": 7, "sierpnia": 8, "września": 9, "pazdziernika": 10,
    "października": 10, "listopada": 11, "grudnia": 12,
}

REL_RE = re.compile(
    r"(dzisiaj|teraz|wczoraj|\d+\s*(?:minut|min|godzin|godz|dni|tygodni|tydz|mesi|mes)\w*(?:\s*temu)?)",
    re.I,
)
ABS_RE = re.compile(
    r"(?<!\d)(\d{4})-(\d{2})-(\d{2})(?!\d)"
    r"|(?<!\d)(\d{1,2})[./-](\d{1,2})[./-](\d{2,4})(?!\d)"
    r"|(?<!\d)(\d{1,2})\s+([a-ząćęłńóśźż]+)\s+(\d{4})(?!\d)",
    re.I,
)
DEADLINE_RE = re.compile(
    r"(?:termin|terminu|aplikuj\w*|ważna|ważne|ważność)\s*(?:do|:)?\s*"
    r"(\d{1,2}[./-]\d{1,2}(?:[./-]\d{2,4})?|\d{1,2}\s+[a-ząćęłńóśźż]+\s+\d{4})",
    re.I,
)


def _text_only(text: str) -> str:
    t = re.sub(r"<style[\s\S]*?</style>", " ", text or "", flags=re.I)
    t = re.sub(r"<[^>]+>", " ", t)
    return clean(t)


def _iso(year: int, month: int, day: int) -> str:
    if year < 100:
        year += 2000 if year < 70 else 1900
    if not (1 <= month <= 12 and 1 <= day <= 31 and 1990 <= year <= 2100):
        return ""
    return f"{year:04d}-{month:02d}-{day:02d}"


def _abs_to_iso(frag: str) -> str:
    for m in ABS_RE.finditer(frag or ""):
        g = m.groups()
        if g[0]:
            iso = _iso(int(g[0]), int(g[1]), int(g[2]))
        elif g[3]:
            iso = _iso(int(g[5]), int(g[4]), int(g[3]))
        else:
            iso = _iso(int(g[8]), MONTHS.get(g[7].lower(), 0), int(g[6]))
        if iso:
            return iso
    return ""


def post_date(text: str) -> str:
    """Data ogloszenia jako ISO. Kolejnosc: wzgledna (dzisiaj/3 dni temu), potem bezwzgledna."""
    t = _text_only(text)
    if not t:
        return ""
    m = REL_RE.search(t)
    if m:
        frag = m.group(1).lower()
        today = date.today()
        if "wczoraj" in frag:
            return (today - timedelta(days=1)).isoformat()
        n = re.match(r"(\d+)\s*(min|godz|dni|tyg|mes)", frag)
        if n:
            amount = int(n.group(1))
            unit = n.group(2)
            days = 0
            if unit == "dni":
                days = amount
            elif unit == "tyg":
                days = amount * 7
            elif unit == "mes":
                days = amount * 30
            return (today - timedelta(days=days)).isoformat()
        return today.isoformat()
    return _abs_to_iso(t)


def deadline_from(text: str) -> str:
    """Termin aplikacji jako ISO, jesli jest w tekście; inaczej pusty string."""
    t = _text_only(text)
    if not t:
        return ""
    m = DEADLINE_RE.search(t)
    return _abs_to_iso(m.group(1)) if m else ""


def run_all_sources(names: list[str] | None = None) -> dict[str, list[dict]]:
    """Uruchamia scrapery; zwraca {source: [jobs...]} z uzasadnieniem bledow."""
    results: dict[str, list[dict]] = {}
    for name, fn in REGISTRY.items():
        if names and name not in names:
            continue
        try:
            results[name] = fn() or []
        except Exception as e:  # scraper pada — nie przerywaj calosci
            results[name] = []
            results[f"__error__{name}"] = str(e)
    return results
