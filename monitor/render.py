"""Generuje index.html — stonowany, spokojny layout (karty, ciepła paleta)."""
from __future__ import annotations

import html
import re
import unicodedata
from datetime import date
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

_CSS = """
:root {
  --bg: #f7f4f2;
  --surface: #ffffff;
  --ink: #2b2622;
  --ink-soft: #6f6762;
  --ink-faint: #9a918b;
  --line: #e7e0da;
  --accent: #8a4f5c;
  --accent-ink: #6d3b46;
  --accent-wash: #f4ecec;
  --radius: 14px;
  --serif: "Iowan Old Style", "Palatino Linotype", Palatino, Georgia, "Times New Roman", serif;
  --sans: "Segoe UI", system-ui, -apple-system, "Helvetica Neue", sans-serif;
}
* { box-sizing: border-box; }
html { -webkit-text-size-adjust: 100%; }
body {
  margin: 0;
  font-family: var(--sans);
  font-size: 16px;
  line-height: 1.6;
  color: var(--ink);
  background: var(--bg);
}
h1, h2, h3 { font-family: var(--serif); font-weight: 600; letter-spacing: -0.01em; }

header {
  background: linear-gradient(150deg, #8a4f5c 0%, #6d3b46 55%, #5b3039 100%);
  color: #fdf8f7;
  padding: 3rem 1.25rem 2.6rem;
  text-align: center;
}
header h1 {
  margin: 0 0 .5rem;
  font-size: clamp(1.7rem, 4.5vw, 2.4rem);
  font-weight: 600;
}
header .sub { margin: 0 auto; max-width: 42ch; opacity: .88; font-size: .95rem; }
header .facts {
  margin: 1.1rem 0 0;
  font-size: .85rem;
  opacity: .78;
  letter-spacing: .02em;
}

nav {
  position: sticky;
  top: 0;
  z-index: 20;
  display: flex;
  gap: .45rem;
  padding: .7rem 1rem;
  background: rgba(247, 244, 242, .92);
  backdrop-filter: blur(8px);
  border-bottom: 1px solid var(--line);
  overflow-x: auto;
  scrollbar-width: thin;
}
.tab {
  flex: 0 0 auto;
  font: inherit;
  font-size: .85rem;
  font-weight: 600;
  color: var(--accent-ink);
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: 999px;
  padding: .38rem .85rem;
  cursor: pointer;
  white-space: nowrap;
  transition: background .15s, color .15s, border-color .15s;
}
.tab:hover { border-color: var(--accent); color: var(--accent); }
.tab.active {
  background: var(--accent);
  border-color: var(--accent);
  color: #fff;
}
.tab:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }

main { max-width: 860px; margin: 0 auto; padding: 2rem 1.1rem 3.5rem; }
.tab-panel { display: none; }
.tab-panel.active { display: block; }
section + section, .tab-panel > section + section { margin-top: 2.4rem; }

h2 {
  display: flex;
  align-items: baseline;
  gap: .6rem;
  margin: 0 0 1rem;
  font-size: 1.22rem;
}
h2::before {
  content: "";
  width: .5rem;
  height: .5rem;
  border-radius: 50%;
  background: var(--accent);
  transform: translateY(-.15rem);
}
.count { font-family: var(--sans); font-size: .82rem; font-weight: 600; color: var(--ink-faint); }

.cards { display: flex; flex-direction: column; gap: .6rem; }
.offer {
  display: grid;
  grid-template-columns: minmax(0, 1fr) auto;
  gap: .4rem 1rem;
  align-items: center;
  padding: .95rem 1.1rem;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--radius);
  transition: border-color .15s, box-shadow .15s, transform .15s;
}
.offer:hover {
  border-color: #d8c9c4;
  box-shadow: 0 4px 16px rgba(60, 40, 40, .07);
  transform: translateY(-1px);
}
.offer-title { margin: 0; font-size: 1.05rem; line-height: 1.35; }
.offer-title a { color: inherit; text-decoration: none; }
.offer-title a:hover { color: var(--accent); }
.offer-title a:focus-visible { outline: 2px solid var(--accent); outline-offset: 3px; border-radius: 3px; }
.offer-meta {
  margin: .2rem 0 0;
  font-size: .84rem;
  color: var(--ink-soft);
}
.offer-meta .sep { color: var(--ink-faint); margin: 0 .45rem; }
.offer-side {
  display: flex;
  align-items: center;
  gap: .7rem;
  justify-self: end;
}
.pay { font-weight: 600; font-size: .92rem; color: var(--accent-ink); white-space: nowrap; }
.cta {
  font-size: .8rem;
  font-weight: 600;
  text-decoration: none;
  color: var(--accent);
  border: 1px solid #dfd0cb;
  border-radius: 999px;
  padding: .3rem .75rem;
  white-space: nowrap;
}
.cta:hover { background: var(--accent); border-color: var(--accent); color: #fff; }
.cta:focus-visible { outline: 2px solid var(--accent); outline-offset: 2px; }

#nowe .offer { border-left: 3px solid var(--accent); }
.gap {
  display: flex;
  align-items: center;
  gap: .8rem;
  margin: 1.6rem 0 1rem;
  color: var(--ink-faint);
  font-size: .82rem;
}
.gap::before, .gap::after { content: ""; flex: 1; border-top: 1px dashed var(--line); }
.empty {
  padding: 1.1rem;
  background: var(--surface);
  border: 1px dashed var(--line);
  border-radius: var(--radius);
  color: var(--ink-faint);
  font-size: .9rem;
  font-style: italic;
}
footer {
  border-top: 1px solid var(--line);
  padding: 1.8rem 1.25rem 2.5rem;
  text-align: center;
  color: var(--ink-faint);
  font-size: .82rem;
}
footer strong { color: var(--ink-soft); font-weight: 600; }

@media (max-width: 640px) {
  .offer { grid-template-columns: 1fr; }
  .offer-side { justify-self: start; margin-top: .5rem; }
  header { padding: 2.2rem 1.1rem 2rem; }
  h2 { font-size: 1.12rem; }
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


def _card(d: dict) -> str:
    url = d.get("url", "")
    title = _esc(d.get("title", ""))
    company = _esc(d.get("company") or "")
    meta: list[str] = []
    if company and company != "—":
        meta.append(company)
    meta.append(_esc(_host(url)))
    posted = _fmt_date(d.get("posted_at", ""))
    if posted:
        meta.append(posted)
    deadline = _fmt_date(d.get("deadline", ""))
    if deadline:
        meta.append(f"termin {deadline}")
    pay = _esc((d.get("salary_raw") or "").strip())
    pay_html = f'<span class="pay">{pay}</span>' if pay else ""
    cta = (
        f'<a class="cta" href="{_esc(url)}" target="_blank" rel="noopener">Zobacz</a>'
        if url
        else ""
    )
    meta_html = '<span class="sep">·</span>'.join(meta)
    title_html = (
        f'<a href="{_esc(url)}" target="_blank" rel="noopener">{title}</a>'
        if url
        else title
    )
    return (
        '      <article class="offer">\n'
        '        <div>\n'
        f'          <h3 class="offer-title">{title_html}</h3>\n'
        f'          <p class="offer-meta">{meta_html}</p>\n'
        "        </div>\n"
        f'        <div class="offer-side">{pay_html}{cta}</div>\n'
        "      </article>\n"
    )


def _cards(items: list[dict], empty_msg: str) -> str:
    if not items:
        return f'    <p class="empty">{_esc(empty_msg)}</p>\n'
    return '    <div class="cards">\n' + "".join(_card(d) for d in items) + "    </div>\n"


def render(
    rows,
    out_path: str | Path | None = None,
    recent_ids: set | frozenset = frozenset(),
) -> Path:
    """rows: iterable sqlite3.Row / dict. recent_ids: (source, external_id) nowych."""
    by_day: dict[str, dict[str, list]] = {}
    new_items: list[dict] = []
    total = 0
    today_iso = date.today().isoformat()
    today_n = 0
    for r in rows:
        d = dict(r)
        if not d.get("title"):
            continue
        pub = (d.get("posted_at") or d.get("first_seen_at") or "")[:10] or "bez-daty"
        sec = _section(d.get("title", ""))
        by_day.setdefault(pub, {sid: [] for sid, _ in SECTIONS})[sec].append(d)
        if (d.get("source"), d.get("external_id")) in recent_ids:
            new_items.append(d)
        if pub == today_iso:
            today_n += 1
        total += 1

    new_items.sort(
        key=lambda x: (x.get("posted_at") or "", _norm(x.get("title", ""))), reverse=True
    )
    today = date.today().strftime("%d.%m.%Y")

    day_keys = sorted((k for k in by_day if k != "bez-daty"), reverse=True)
    if "bez-daty" in by_day:
        day_keys.append("bez-daty")

    def _day_label(k: str) -> str:
        if k == "bez-daty":
            return "bez daty"
        try:
            y, m, d = (int(x) for x in k.split("-"))
            return f"{_WD[date(y, m, d).weekday()]} {d:02d}.{m:02d}"
        except ValueError:
            return k

    tabs = [
        f'<button type="button" class="tab active" data-t="nowe">Nowe ({len(new_items)})</button>'
    ]
    for k in day_keys:
        n = sum(len(v) for v in by_day[k].values())
        tabs.append(
            f'<button type="button" class="tab" data-t="d-{_esc(k)}">'
            f"{_esc(_day_label(k))} ({n})</button>"
        )
    nav = "\n  ".join(tabs)

    parts: list[str] = [f"""<!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="Aktualne oferty pracy w Przemyślu dla kobiety — sprzedaż, gastronomia, farmacja, produkcja. Bez pracy biurowej, budżetówki i administracji.">
<meta name="theme-color" content="#8a4f5c">
<title>Oferty pracy w Przemyślu</title>
<style>{_CSS}</style>
</head>
<body>

<header>
  <h1>Oferty pracy w Przemyślu</h1>
  <p class="sub">Praca dla kobiety — sprzedaż, obsługa klienta, gastronomia, uroda
     i lekka produkcja. Bez biura, budżetówki i administracji.</p>
  <p class="facts">{total} ofert · {today_n} z dzisiaj · odświeżono {today}</p>
</header>

<nav>
  {nav}
</nav>

<main>

<section id="nowe" class="tab-panel active">
  <h2>Nowe oferty <span class="count">({len(new_items)})</span></h2>
"""]

    fresh = [d for d in new_items if (d.get("posted_at") or d.get("first_seen_at") or "")[:10] == today_iso]
    older = [d for d in new_items if d not in fresh]
    if fresh:
        parts.append(_cards(fresh, ""))
    if older:
        if fresh:
            parts.append(
                f'  <p class="gap">z ostatnich dni ({len(older)})</p>\n'
            )
        parts.append(_cards(older, ""))
    if not new_items:
        parts.append(_cards([], "Brak nowych ofert od ostatniego skanu."))
    parts.append("</section>\n\n")

    for k in day_keys:
        parts.append(f'<div id="d-{_esc(k)}" class="tab-panel">\n')
        for sid, label in SECTIONS:
            items = sorted(by_day[k][sid], key=lambda x: _norm(x.get("title", "")))
            if not items:
                continue
            parts.append(
                f'  <section>\n    <h2>{_esc(label)} '
                f'<span class="count">({len(items)})</span></h2>\n'
            )
            parts.append(_cards(items, ""))
            parts.append("  </section>\n")
        parts.append("</div>\n\n")

    parts.append(f"""</main>

<footer>
  <p><strong>Oferty pracy w Przemyślu</strong> · {total} ofert · {today}</p>
  <p>Sprawdzane automatycznie kilka razy dziennie. Każdy link prowadzi prosto do ogłoszenia.<br>
  Pominięte: praca biurowa, budżetówka, państwówka, administracja, urzędy.</p>
</footer>

<script>
  document.querySelectorAll('.tab').forEach(function (b) {{
    b.addEventListener('click', function () {{
      document.querySelectorAll('.tab').forEach(function (x) {{ x.classList.remove('active'); }});
      document.querySelectorAll('.tab-panel').forEach(function (p) {{ p.classList.remove('active'); }});
      b.classList.add('active');
      document.getElementById(b.dataset.t).classList.add('active');
      window.scrollTo({{ top: 0, behavior: 'smooth' }});
    }});
  }});
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