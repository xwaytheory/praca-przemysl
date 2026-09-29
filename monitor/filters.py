"""Filtr ofert: kobiety / zero biura, budżetówki, państwowki, administracji."""
import unicodedata

from config import CITY_OK, EXCLUDE, INCLUDE, WHITELIST_ON


def _norm(s: str) -> str:
    s = (s or "").lower()
    s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    return s


def passes(job: dict) -> tuple[bool, str]:
    """(True, '') jeśli oferta ma przejść; (False, powód) jeśli odrzucona."""
    title = _norm(job.get("title", ""))
    company = _norm(job.get("company", ""))
    city = _norm(job.get("city", ""))
    url = _norm(job.get("url", ""))
    blob = f"{title} {company} {city} {url}"

    for x in EXCLUDE:
        xn = _norm(x)
        if xn and xn in blob:
            return False, f"exclude:{xn}"

    if city:
        if not any(ok in city for ok in CITY_OK) and city.strip() not in ("", "-"):
            if not any(
                k in city
                for k in (
                    "podkarpack",
                    "medyk",
                    "orly",
                    "borek",
                    "lubaczow",
                    "jaroslaw",
                    "arlamow",
                    "polska",
                    "+",
                )
            ):
                return False, f"city:{city}"

    if WHITELIST_ON:
        if not any(_norm(w) in title for w in INCLUDE):
            return False, "no-whitelist"
    return True, ""
