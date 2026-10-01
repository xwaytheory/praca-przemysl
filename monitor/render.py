"""Generuje index.html: tabele ofert (na telefonie -> karty przez CSS), zakładki po dniach."""
from __future__ import annotations

import html
import re
import unicodedata
from datetime import date, datetime
from pathlib import Path
from urllib.parse import urlparse

from config import HTML_OUT

# sekcje (branże) — tak jak w przykładzie index.html
SECTIONS = (
    ("farmacja", "Farmacja, zdrowie, uroda"),
    ("sprzedaz", "Sprzedaż, obsługa klienta, handel"),
    ("gastronomia", "Gastronomia, hotelarstwo, usługi"),
    ("pozostale", "Magazyn, produkcja, opiekun i pozostałe"),
)

_W = {
    "farmacja": (
        "farmac", "aptek", "magister farmacji", "technik farmacji",
        "pielęgniar", "pielegniar", "fizjoterapeut", "kosmetolog",
        "kosmetyczk", "fryzjer", "stylistk", "stylista", "paznokci",
        "makijaz", "makijaż", "masaz", "masaż", "uroda", "pielęgnacj",
        "pielegnacj", "pracownik medyczny", "zdrow",
    ),
    "sprzedaz": (
        "sprzedaz", "sprzedaż", "sprzedawc", "kasjer", "ekspedient",
        "obsługa klienta", "obsluga klienta", "doradca klienta", "handlow",
        "sklep", "salon", "stoisko", "hostess", "promotor", "ambasador",
        "kierownik sklepu", "kierownik zmiany", "lider", "wykładanie",
        "wykladanie", "przyjmowanie towar", "sprzeda", "logistyk",
        "pracownik hali", "inwentaryzacj", "obsług", "obslug",
    ),
    "gastronomia": (
        "kelner", "kucharz", "gastronom", "barman", "barist", "restauracj",
        "pomoc kuchenna", "piekarz", "cukiernik", "hotel", "pokojowa",
        "pokojowy", "recepcjonist", "housekeeping", "sprząt", "sprzat",
        "pralnia", "ratownik", "obsługa gości", "obsluga gosci",
        "pracownik restauracji", "pracownik hotel", "staff", "crew",
        "kebab", "pizzer",
    ),
    "pozostale": (),  # domyślny zrzut
}

_WD = ("pon", "wt", "śr", "czw", "pt", "sob", "ndz")
MAX_DAYS = 10  # tyle ostatnich dni dostaje własną zakładkę, reszta wchodzi do „Starsze"

# portale w kolejności wiarygodności (przy duplikatach wygrywa lepsze źródło)
_SRC_PRIORITY = (
    "pracuj", "egospodarka", "pracapl", "gowork", "przemyslpraca",
    "olx", "nuzle", "ogloszeniaprz", "infopraca", "kariera",
)
_PLACEHOLDER = (
    "osoba prywatna", "pracodawca nie podany", "klient portalu", "baza ofert",
    "praca.farmacja", "centralna baza", "ogloszeniaprzemysl", "pracuj.pl", "praca.pl",
)
_MONEY = re.compile(
    r"(?:(?:od|do|ok\.)\s*)?\d[\d\s.,]*\s*(?:zł|zl|€|eur|pln)"
    r"(?:\s*[-–]\s*\d[\d\s.,]*\s*(?:zł|zl|€|eur|pln)?)?"
    r"(?:\s*/\s*(?:h|godz|godzin|mies|rok|dn))?"
    r"(?:\s*(?:netto|brutto))?",
    re.I,
)
_HAS_UNIT = re.compile(r"/|h\b|godz|mies|dn|rok", re.I)

_CSS = """
:root {
  --bg: #f1ece8;
  --surface: #ffffff;
  --ink: #2b2622;
  --ink-soft: #5f5854;
  --ink-faint: #6d6461;
  --line: #e3dad3;
  --line-strong: #94806f;
  --accent: #8a4f5c;
  --accent-ink: #6d3b46;
  --accent-wash: #f2e7e8;
  --zebra: #faf7f6;
  --radius: 12px;
  --nav-h: 61px;
  --serif: "Iowan Old Style", "Palatino Linotype", Palatino, Georgia, "Times New Roman", serif;
  --sans: "Segoe UI", system-ui, -apple-system, "Helvetica Neue", sans-serif;
}
* { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; scroll-padding-top: calc(var(--nav-h) + 1rem); }
body {
  margin: 0;
  font-family: var(--sans);
  font-size: 16px;
  line-height: 1.55;
  color: var(--ink);
  background: var(--bg);
}
h1, h2 { font-family: var(--serif); font-weight: 600; letter-spacing: -0.015em; }
h1 { font-size: clamp(1.8rem, 4.6vw, 2.4rem); line-height: 1.15; margin: 0 0 .6rem; }
h2 { font-size: 1.35rem; line-height: 1.2; margin: 0 0 .9rem; }
h3 { font-family: var(--sans); font-size: .95rem; font-weight: 650; margin: 0 0 .5rem; }
a { color: var(--accent-ink); }

.sr-only {
  position: absolute; width: 1px; height: 1px; padding: 0; margin: -1px;
  overflow: hidden; clip-path: inset(50%); white-space: nowrap; border: 0;
}
.skip { position: absolute; left: -9999px; }
.skip:focus { position: static; display: inline-block; padding: .5rem; background: #fff; }

header {
  background: linear-gradient(160deg, #75424e 0%, #5f343d 100%);
  color: #fdf8f7;
  padding: 2.4rem 1.25rem 2.1rem;
  text-align: center;
}
header .sub { margin: 0 auto; max-width: 46ch; opacity: .95; font-size: .95rem; }
header .facts { margin: 1rem 0 0; opacity: .9; font-size: .875rem; letter-spacing: .01em; }

nav {
  position: sticky;
  top: 0;
  z-index: 20;
  padding: 8px 1rem;
  background: rgba(241, 236, 232, .95);
  backdrop-filter: blur(8px);
  border-bottom: 1px solid var(--line);
}
nav .row { display: flex; gap: .4rem; overflow-x: auto; scrollbar-width: thin; }
.tab {
  flex: 0 0 auto;
  font: inherit;
  font-size: .875rem;
  font-weight: 600;
  color: var(--accent-ink);
  background: var(--surface);
  border: 1px solid var(--line-strong);
  border-radius: 999px;
  padding: .5rem .9rem;
  min-height: 44px;
  cursor: pointer;
  white-space: nowrap;
  transition: background .15s, color .15s, border-color .15s;
}
.tab:hover { border-color: var(--accent); color: var(--accent); }
.tab.active { background: var(--accent); border-color: var(--accent); color: #fff; }
.tab:focus-visible, a:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }

main { max-width: 1020px; margin: 0 auto; padding: 1.6rem 1.1rem 3rem; }
.tab-panel { display: block; }
.tab-panel[hidden] { display: none; }
section + section { margin-top: 2rem; }
h2 { display: flex; align-items: center; gap: .6rem; flex-wrap: wrap; }
h2::before {
  content: "";
  width: .5rem;
  height: .5rem;
  border-radius: 50%;
  background: var(--accent);
  flex: 0 0 auto;
}
.count { font-family: var(--sans); font-size: .82rem; font-weight: 600; color: var(--ink-faint); }

.table-wrap {
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  overflow: clip; /* clip, nie hidden — hidden zabija position:sticky w thead */
}
.tbl { width: 100%; border-collapse: separate; border-spacing: 0; font-size: .95rem; }
.tbl th {
  text-align: left;
  font-size: .74rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .05em;
  color: var(--ink-soft);
  padding: .55rem .8rem;
  background: var(--accent-wash);
  border-bottom: 1px solid var(--line);
  white-space: nowrap;
}
.tbl td { padding: .6rem .8rem; border-bottom: 1px solid var(--line); vertical-align: top; }
.tbl tbody tr:last-child td { border-bottom: 0; }
.tbl tbody tr:nth-child(even) { background: var(--zebra); }
.tbl tbody tr:hover { background: var(--accent-wash); }
.tbl .t { font-weight: 650; line-height: 1.35; overflow-wrap: anywhere; }
.tbl .t a { color: inherit; text-decoration: none; display: inline-block; min-height: 24px; }
.tbl .t a:hover { color: var(--accent-ink); text-decoration: underline; text-underline-offset: 3px; }
.tbl .t small { display: block; margin-top: .15rem; font-size: .8em; font-weight: 400; color: var(--ink-faint); }
.tbl .num { text-align: right; white-space: nowrap; font-variant-numeric: tabular-nums; }
.tbl .pay { color: var(--accent-ink); font-weight: 650; }
.tbl .pay.none { color: var(--ink-faint); font-weight: 400; }
.tbl .d { white-space: nowrap; font-variant-numeric: tabular-nums; color: var(--ink-soft); }
.tbl .d small { color: var(--ink-faint); }
.tbl .go { text-align: right; white-space: nowrap; }
.go a {
  display: inline-block;
  font-size: .82rem;
  font-weight: 600;
  text-decoration: none;
  color: var(--accent-ink);
  border: 1px solid var(--line-strong);
  border-radius: 999px;
  padding: .4rem .75rem;
  min-height: 36px;
}
.go a:hover { background: var(--accent); border-color: var(--accent); color: #fff; }
.badge-new {
  display: inline-block;
  font-size: .68rem;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: .06em;
  color: #fff;
  background: var(--accent);
  border-radius: 999px;
  padding: .12rem .45rem;
  margin-right: .45rem;
  vertical-align: .12em;
}

.gap {
  display: flex;
  align-items: center;
  gap: .8rem;
  margin: 1.5rem 0 .9rem;
  color: var(--ink-faint);
  font-size: .82rem;
}
.gap::before, .gap::after { content: ""; flex: 1; border-top: 1px dashed var(--line-strong); }
.empty {
  padding: 1rem 1.1rem;
  background: var(--surface);
  border: 1px dashed var(--line-strong);
  border-radius: var(--radius);
  color: var(--ink-soft);
  font-size: .9rem;
}
.legend { margin: .5rem .2rem 0; color: var(--ink-faint); font-size: .8rem; }
footer {
  border-top: 1px solid var(--line);
  padding: 1.6rem 1.25rem 2.2rem;
  text-align: center;
  color: var(--ink-faint);
  font-size: .82rem;
}
footer strong { color: var(--ink-soft); }
@media (prefers-reduced-motion: reduce) {
  * { transition-duration: .01ms !important; scroll-behavior: auto !important; }
}

@media (min-width: 720px) {
  .tbl thead th { position: sticky; top: var(--nav-h); z-index: 5; }
}

/* Telefon: ta sama tabela jako karty. Nagłówek kolumn zostaje w drzewie
   dostępności (sr-only), bo inaczej czytnik ekranu traci nazwy kolumn. */
@media (max-width: 719px) {
  html { font-size: 17px; }
  .tbl, .tbl tbody, .tbl tr, .tbl td { display: block; }
  .tbl thead { position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%); }
  .tbl tr { padding: .7rem .85rem; border-bottom: 1px solid var(--line); }
  .tbl tr:last-child { border-bottom: 0; }
  .tbl td { border: 0; padding: .1rem 0; font-size: .875rem; color: var(--ink-soft); }
  .tbl td::before {
    content: attr(data-l);
    display: block;
    font-size: .7rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: .05em;
    color: var(--ink-faint);
  }
  .tbl td.t { display: block; font-size: 1.02rem; color: var(--ink); margin-bottom: .3rem; }
  /* clamp tylko na sam tytuł — firma pod spodem musi zostać widoczna */
  .tbl td.t > a {
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
  .tbl td.t::before, .tbl td.go::before { content: none; }
  .tbl td.num, .tbl td.d {
    text-align: left;
    display: flex;
    gap: .55rem;
    white-space: normal;
  }
  .tbl td.num::before, .tbl td.d::before { flex: 0 0 6.6rem; padding-top: .12rem; }
  .tbl td.num > span, .tbl td.d > span { min-width: 0; overflow-wrap: anywhere; text-align: left; }
  .tbl td.go { display: block; margin-top: .55rem; }
  .go a {
    display: block;
    text-align: center;
    background: var(--accent);
    border-color: var(--accent);
    color: #fff;
    padding: .6rem 1rem;
    min-height: 44px;
  }
}
@media (hover: none) {
  .tbl .t a { text-decoration: underline; text-underline-offset: 2px; }
}
"""


def _norm(s: str) -> str:
    s = (s or "").lower()
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def _section(title: str) -> str:
    t = _norm(title)
    for sid, words in _W.items():
        if sid == "pozostale":
            continue
        if any(_norm(w) in t for w in words):
            return sid
    return "pozostale"


def _esc(s: str) -> str:
    return html.escape(s or "", quote=True)


def _host(url: str) -> str:
    try:
        h = urlparse(url).netloc.replace("www.", "")
        return h.split(":")[0] or "ogłoszenie"
    except Exception:
        return "ogłoszenie"


def _fmt_date(value: str) -> str:
    """'2026-09-28' -> '28.09' (z rokiem tylko dla poprzednich lat)."""
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", (value or "").strip())
    if not m:
        return ""
    y, mo, d = (int(g) for g in m.groups())
    try:
        if date(y, mo, d).year != date.today().year:
            return f"{d:02d}.{mo:02d}.{y}"
    except ValueError:
        return ""
    return f"{d:02d}.{mo:02d}"


def _ymd(iso: str) -> int:
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", iso or "")
    if not m:
        return 0
    y, mo, d = (int(g) for g in m.groups())
    return y * 10000 + mo * 100 + d


def _pay_text(d: dict) -> str:
    """Kwota z salary_raw; gdy nie ma w niej jednostki, bierzemy dosłowny fragment
    z tytułu („do 82 zł/h”). Nigdy nie doklejamy jednostki, której nie ma."""
    raw = (d.get("salary_raw") or "").strip()
    m = _MONEY.search(d.get("title", "") or "")
    from_title = re.sub(r"\s+", " ", m.group(0)).strip() if m else ""
    if raw and _HAS_UNIT.search(raw):
        return raw
    if from_title and _HAS_UNIT.search(from_title):
        return from_title
    return raw or from_title


def _clean_company(raw: str) -> str:
    """'Osoba prywatna' / 'Pracodawca nie podany' to szum — zwracamy pusty string."""
    c = (raw or "").strip()
    if not c or c == "—":
        return ""
    low = _norm(c)
    if any(p in low for p in _PLACEHOLDER):
        return ""
    return c


def _row(d: dict, badge: bool = False) -> str:
    url = d.get("url", "")
    title = _esc(d.get("title", ""))
    company = _esc(_clean_company(d.get("company", "")))
    pay = _pay_text(d)
    pay_html = (
        f'<span class="pay">{_esc(pay)}</span>' if pay else '<span class="pay none">—</span>'
    )
    posted = (d.get("posted_at") or "").strip()
    seen = (d.get("first_seen_at") or "")[:10]
    if posted:
        d_lbl, d_html = "Opublikowano", _esc(_fmt_date(posted))
    else:
        d_lbl = "Znaleziono"
        d_html = (
            f'{_esc(_fmt_date(seen))}<small> (bez daty)<span class="sr-only"> — portal nie udostępnił '
            "daty publikacji, to data znalezienia oferty</span></small>"
        )
    host = _esc(_host(url))
    title_html = (
        f'<a href="{_esc(url)}" target="_blank" rel="noopener">{title}'
        '<span class="sr-only"> — otwiera ogłoszenie w nowym oknie</span></a>'
        if url
        else title
    )
    dupes = int(d.get("_dupes") or 1)
    sub = ""
    if company:
        sub += f'<small>{company}</small>'
    if dupes > 1:
        sub += (
            f'<small>{host} +{dupes - 1}<span class="sr-only"> — ogłoszenie powtórzone na '
            f"{dupes - 1} innych portalach</span></small>"
        )
    new_badge = '<span class="badge-new">nowe</span>' if badge and d.get("_is_new") else ""
    return (
        "        <tr>"
        f'<td class="t" data-l="">{new_badge}{title_html}{sub}</td>'
        f'<td class="num" data-l="Płaca">{pay_html}</td>'
        f'<td class="d" data-l="{d_lbl}"><span>{d_html}</span></td>'
        f'<td class="go" data-l=""><a href="{_esc(url)}" target="_blank" rel="noopener">{host}'
        f'<span class="sr-only"> — ogłoszenie: {title} (otwiera nowe okno)</span></a></td>'
        "</tr>\n"
    )


def _table(items: list[dict], caption: str, badge: bool = False) -> str:
    if not items:
        return f'    <p class="empty">{_esc(caption)}</p>\n'
    return (
        '    <div class="table-wrap">\n'
        '    <table class="tbl">\n'
        f'      <caption class="sr-only">{_esc(caption)}</caption>\n'
        "      <thead><tr>"
        '<th scope="col">Stanowisko</th>'
        '<th scope="col" class="num">Płaca</th>'
        '<th scope="col">Data</th>'
        '<th scope="col">Ogłoszenie</th>'
        "</tr></thead>\n"
        "      <tbody>\n"
        + "".join(_row(d, badge) for d in items)
        + "      </tbody>\n    </table>\n    </div>\n"
    )


def _sort_key(d: dict):
    """Najnowsze pierwsze, potem alfabetycznie (pensja występuje w 2% rekordów)."""
    iso = (d.get("posted_at") or d.get("first_seen_at") or "")[:10]
    return (-_ymd(iso), _norm(d.get("title", "")))


def _collect(rows) -> tuple[dict, int]:
    """Zwraca (by_day, total).

    Dedupe tylko między RÓŻNYMI portalami i tylko przy identycznym pełnym tytule
    oraz identycznej firmie (pusta == pusta). Dwa ogłoszenia z tego samego portalu
    o różnym external_id to dwie różne oferty (inna ekipa, inne miasto) — nie scalamy.
    """
    raw = []
    for r in rows:
        d = dict(r)
        if d.get("title"):
            raw.append(d)

    # wybór najlepszego rekordu w grupie: prawdziwa data > prawdziwa firma > źródło > nowość
    raw.sort(
        key=lambda d: (
            0 if (d.get("posted_at") or "").strip() else 1,
            0 if _clean_company(d.get("company", "")) else 1,
            _SRC_PRIORITY.index(d["source"]) if d["source"] in _SRC_PRIORITY else 99,
            -_ymd((d.get("posted_at") or d.get("first_seen_at") or "")[:10]),
        )
    )
    seen: dict[tuple[str, str], dict] = {}
    for d in raw:
        key = (_norm(d["title"]), _norm(_clean_company(d.get("company", ""))))
        hit = seen.get(key)
        if hit is None:
            d["_dupes"] = 1
            seen[key] = d
        elif hit["source"] != d["source"]:  # to samo ogłoszenie na innym portalu
            hit["_dupes"] += 1

    by_day: dict[str, dict[str, list]] = {}
    for d in seen.values():
        day = (d.get("posted_at") or d.get("first_seen_at") or "")[:10] or "bez-daty"
        by_day.setdefault(day, {sid: [] for sid, _ in SECTIONS})[_section(d["title"])].append(d)
    return by_day, len(seen)


def _scan_label(scan_at: str) -> str:
    """'2026-10-01 10:00:00' (UTC z meta) -> '1.10 o 12:00' czasu polskiego, gdy da się."""
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})[ T](\d{2}):(\d{2})", scan_at or "")
    if not m:
        return ""
    y, mo, d, hh, mm = (int(g) for g in m.groups())
    try:
        from zoneinfo import ZoneInfo

        dt = datetime(y, mo, d, hh, mm, tzinfo=ZoneInfo("UTC")).astimezone(ZoneInfo("Europe/Warsaw"))
        return f"{dt.day}.{dt.month} o {dt:%H:%M}"
    except Exception:
        return f"{d}.{mo} o {hh:02d}:{mm:02d} UTC"


def render(
    rows,
    out_path: str | Path | None = None,
    recent_ids: set | frozenset = frozenset(),
    scan_at: str = "",
) -> Path:
    """rows: iterable sqlite3.Row / dict. recent_ids: (source, external_id) nowych."""
    by_day, total = _collect(rows)
    by_id = {
        (d.get("source"), d.get("external_id")): d
        for bucket in by_day.values()
        for rows_ in bucket.values()
        for d in rows_
    }
    for k, d in by_id.items():
        d["_is_new"] = k in recent_ids
    new_items = sorted([d for k, d in by_id.items() if k in recent_ids], key=_sort_key)

    today_iso = date.today().isoformat()
    today_n = sum(len(v) for k, b in by_day.items() if k == today_iso for v in b.values())

    all_days = sorted((k for k in by_day if k != "bez-daty"), reverse=True)
    if "bez-daty" in by_day:
        all_days.append("bez-daty")
    day_keys, older_days = all_days[:MAX_DAYS], all_days[MAX_DAYS:]

    def _day_label(k: str) -> str:
        if k == "bez-daty":
            return "data nieznana"
        try:
            y, m, d = (int(x) for x in k.split("-"))
            return f"{_WD[date(y, m, d).weekday()]} {d:02d}.{m:02d}"
        except ValueError:
            return k

    def _tab_caption(k: str) -> str:
        """Jeśli większość dnia to 'znaleziono', zakładka musi to sygnalizować."""
        label = _day_label(k)
        items = [d for rows_ in by_day[k].values() for d in rows_]
        found = sum(1 for d in items if not (d.get("posted_at") or "").strip())
        if items and found * 2 > len(items):
            return f"{label} · znalezione"
        return label

    scan = _scan_label(scan_at)
    facts = f"{total} ofert"
    if today_n:
        facts += f" · {today_n} opublikowanych dziś"
    facts += f" · sprawdzone {scan}" if scan else f" · sprawdzone {date.today():%d.%m}"
    facts += " · sprawdzamy 3× dziennie"

    def _tab(tid: str, panel: str, label: str, active: bool) -> str:
        return (
            f'<button type="button" role="tab" id="t-{tid}" aria-controls="{panel}" '
            f'aria-selected="{"true" if active else "false"}" tabindex="{0 if active else -1}" '
            f'class="tab{" active" if active else ""}" data-t="{panel}">{_esc(label)}</button>'
        )

    tabs = [_tab("nowe", "nowe", f"Nowe ({len(new_items)})", True)]
    for k in day_keys:
        n = sum(len(v) for v in by_day[k].values())
        tabs.append(_tab(f"d-{k}", f"d-{k}", f"{_tab_caption(k)} ({n})", False))
    if older_days:
        n = sum(len(v) for k in older_days for v in by_day[k].values())
        tabs.append(_tab("starsze", "starsze", f"Starsze ({n})", False))

    ns_links = ", ".join(
        f'<a href="#d-{_esc(k)}">{_esc(_day_label(k))}</a>' for k in day_keys
    )
    if older_days:
        ns_links += ', <a href="#starsze">starsze</a>'

    legend = (
        "Opublikowano = data z portalu. Znaleziono = data, kiedy oferta wpadła do naszej listy "
        "(niektóre portali nie podają daty)."
    )

    parts: list[str] = [f"""<!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Praca w Przemyślu bez biura i urzędów — {total} ofert, {today_n} opublikowanych dziś. Sprzedaż, obsługa klienta, gastronomia, uroda, magazyn. Link prosto do ogłoszenia.">
<meta name="theme-color" content="#75424e">
<title>Praca w Przemyślu bez biura i urzędów — {total} ofert</title>
<style>{_CSS}</style>
</head>
<body>
<a class="skip" href="#m">Pomiń do ofert</a>

<header>
  <h1>Praca w Przemyślu bez biura i urzędów</h1>
  <p class="sub">Oferty pracy w Przemyślu bez biura, urzędów i budżetówki.
     Klik w tytuł — otwiera ogłoszenie.</p>
  <p class="facts">{_esc(facts)}</p>
</header>

<nav>
  <div class="row" role="tablist" aria-label="Oferty według dnia">
  {"\n  ".join(tabs)}
  </div>
</nav>

<noscript>
  <style>.tab-panel[hidden] {{ display: block !important; }}</style>
  <p class="legend" style="padding:.5rem 1.1rem">Oferty według dni (JavaScript wyłączony):
     {ns_links}</p>
</noscript>

<main id="m" tabindex="-1">

<section id="nowe" class="tab-panel" role="tabpanel" aria-labelledby="t-nowe">
  <h2>Nowe oferty <span class="count">({len(new_items)})</span></h2>
"""]

    fresh = [d for d in new_items if (d.get("posted_at") or d.get("first_seen_at") or "")[:10] == today_iso]
    rest = [d for d in new_items if d not in fresh]
    if fresh:
        parts.append(_table(fresh, "Nowe oferty — z dzisiaj"))
    else:
        parts.append(
            f'    <p class="empty">Sprawdzone {scan or "przed chwilą"} — dziś jeszcze nic nowego. '
            "Poniżej oferta z ostatnich dni, pełna lista w zakładkach po dniach.</p>\n"
        )
    if rest:
        if fresh:
            parts.append(f'  <p class="gap">z wcześniejszych dni ({len(rest)})</p>\n')
        parts.append(_table(rest, "Nowe oferty — z ostatnich dni"))
    parts.append(f'  <p class="legend">{legend}</p>\n')
    parts.append("</section>\n\n")

    for k in day_keys:
        t = _esc(k)
        n = sum(len(v) for v in by_day[k].values())
        parts.append(
            f'<section id="d-{t}" class="tab-panel" role="tabpanel" aria-labelledby="t-d-{t}" hidden>\n'
            f'  <h2>{_esc(_day_label(k))} <span class="count">({n})</span></h2>\n'
        )
        for sid, label in SECTIONS:
            items = sorted(by_day[k][sid], key=_sort_key)
            if not items:
                continue
            parts.append(
                f'  <section>\n    <h3>{_esc(label)} <span class="count">({len(items)})</span></h3>\n'
            )
            parts.append(_table(items, f"{label} — {_day_label(k)}", badge=True))
            parts.append("  </section>\n")
        parts.append("</section>\n\n")

    if older_days:
        n = sum(len(v) for k in older_days for v in by_day[k].values())
        parts.append(
            '<section id="starsze" class="tab-panel" role="tabpanel" '
            'aria-labelledby="t-starsze" hidden>\n'
            f'  <h2>Starsze <span class="count">({n})</span></h2>\n'
        )
        for k in older_days:  # podział per dzień, żeby było widać, co jest skąd
            kn = sum(len(v) for v in by_day[k].values())
            parts.append(
                f'  <section>\n    <h3>{_esc(_day_label(k))} '
                f'<span class="count">({kn})</span></h3>\n'
            )
            for sid, label in SECTIONS:
                items = sorted(by_day[k][sid], key=_sort_key)
                if not items:
                    continue
                parts.append(
                    f'    <h4 style="font-size:.85rem;margin:.8rem 0 .4rem;color:var(--ink-soft)">'
                    f"{_esc(label)} ({len(items)})</h4>\n"
                )
                parts.append(_table(items, f"{label} — {_day_label(k)}", badge=True))
            parts.append("  </section>\n")
        parts.append("</section>\n\n")

    parts.append(f"""</main>

<footer>
  <p><strong>{total} ofert</strong> · sprawdzone {scan or date.today().isoformat()}</p>
  <p>{legend}</p>
  <p>Oferty znikają z portali po kilku dniach — klikaj od razu, nie odkładaj na później.</p>
  <p>Pominięte: praca biurowa, budżetówka, państwówka, administracja, urzędy.</p>
</footer>

<script>
(function () {{
  var tabs = [].slice.call(document.querySelectorAll('.tab'));
  function select(b) {{
    tabs.forEach(function (t) {{
      var on = t === b;
      t.classList.toggle('active', on);
      t.setAttribute('aria-selected', on ? 'true' : 'false');
      t.tabIndex = on ? 0 : -1;
    }});
    [].forEach.call(document.querySelectorAll('.tab-panel'), function (p) {{
      p.hidden = p.id !== b.dataset.t;
    }});
  }}
  tabs.forEach(function (b, i) {{
    b.addEventListener('click', function () {{ select(b); }});
    b.addEventListener('keydown', function (e) {{
      var next = {{
        ArrowRight: tabs[(i + 1) % tabs.length],
        ArrowLeft: tabs[(i - 1 + tabs.length) % tabs.length],
        Home: tabs[0],
        End: tabs[tabs.length - 1]
      }}[e.key];
      if (!next) return;
      next.focus(); select(next); e.preventDefault();
    }});
  }});
  select(tabs[0]);
}})();
</script>

</body>
</html>
""")

    out = Path(out_path or HTML_OUT)
    if not out.is_absolute():
        # HTML_OUT jest ścieżką względną root projektu (rodzic monitor/)
        root = Path(__file__).resolve().parent.parent
        out = root / out
    out.write_text("".join(parts), encoding="utf-8")
    return out