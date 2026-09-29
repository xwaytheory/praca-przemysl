"""Generuje index.html (styl jak istniejący przykład) ze wszystkich ofert w DB."""
from __future__ import annotations

import html
import re
import unicodedata
from datetime import date
from pathlib import Path
from urllib.parse import urlparse

from config import HTML_OUT

# sekcje jak w przykładzie index.html
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
        return h or "link"
    except Exception:
        return "link"


def _pay(salary: str) -> str:
    s = (salary or "").strip()
    if not s:
        return '<td class="pay none">—</td>'
    return f'<td class="pay">{_esc(s)}</td>'


def _link(url: str, source: str, external_id: str) -> str:
    if not url:
        return '<td class="link">—</td>'
    label = f"{_host(url)} {external_id}" if external_id else _host(url)
    if len(label) > 40:
        label = label[:37] + "…"
    return (
        f'<td class="link"><a href="{_esc(url)}" target="_blank" rel="noopener">'
        f"{_esc(label)}</a></td>"
    )


def _date_cell(value: str) -> str:
    v = (value or "").strip()
    if not v:
        return '<td class="date none">—</td>'
    m = re.match(r"^(\d{4})-(\d{2})-(\d{2})", v)
    if m:
        return f'<td class="date">{m.group(3)}.{m.group(2)}.{m.group(1)}</td>'
    return f'<td class="date">{_esc(v)}</td>'


def _table(items: list[dict], empty_msg: str) -> str:
    parts = ['  <div class="table-wrap">\n    <table>\n']
    parts.append(
        "      <thead>\n"
        "        <tr><th>Stanowisko</th><th>Pracodawca</th><th>Płaca</th>"
        "<th>Data</th><th>Termin</th>"
        "<th>Link do ogłoszenia</th></tr>\n"
        "      </thead>\n"
        "      <tbody>\n"
    )
    if not items:
        parts.append(f'        <tr><td colspan="6" class="empty">{empty_msg}</td></tr>\n')
    for d in items:
        title = _esc(d.get("title", ""))
        company = _esc(d.get("company") or "—")
        parts.append(
            f"        <tr><td>{title}</td><td>{company}</td>"
            f"{_pay(d.get('salary_raw', ''))}"
            f"{_date_cell(d.get('posted_at', ''))}"
            f"{_date_cell(d.get('deadline', ''))}"
            f"{_link(d.get('url', ''), d.get('source', ''), d.get('external_id', ''))}</tr>\n"
        )
    parts.append("      </tbody>\n    </table>\n  </div>\n")
    return "".join(parts)


def render(
    rows,
    out_path: str | Path | None = None,
    recent_ids: set | frozenset = frozenset(),
) -> Path:
    """rows: iterable sqlite3.Row / dict. recent_ids: (source, external_id) nowych."""
    by_day: dict[str, dict[str, list]] = {}
    new_items: list[dict] = []
    total = 0
    for r in rows:
        d = dict(r)
        if not d.get("title"):
            continue
        day = ((d.get("posted_at") or d.get("first_seen_at") or "")[:10]) or "bez-daty"
        sec = _section(d.get("title", ""))
        by_day.setdefault(day, {sid: [] for sid, _ in SECTIONS})[sec].append(d)
        if (d.get("source"), d.get("external_id")) in recent_ids:
            new_items.append(d)
        total += 1

    new_items.sort(key=lambda x: (x.get("posted_at") or "", _norm(x.get("title", ""))), reverse=True)
    today = date.today().strftime("%d.%m.%Y")

    day_keys = sorted((k for k in by_day if k != "bez-daty"), reverse=True)
    if "bez-daty" in by_day:
        day_keys.append("bez-daty")
    _WD = ("pon", "wt", "śr", "czw", "pt", "sob", "ndz")

    def _day_label(k: str) -> str:
        if k == "bez-daty":
            return "bez daty"
        try:
            y, m, d = (int(x) for x in k.split("-"))
            return f"{_WD[date(y, m, d).weekday()]} {d:02d}.{m:02d}"
        except ValueError:
            return k

    nav = [
        f'<button type="button" class="tab active" data-t="nowe">Nowe ({len(new_items)})</button>'
    ]
    for k in day_keys:
        n = sum(len(v) for v in by_day[k].values())
        nav.append(
            f'<button type="button" class="tab" data-t="d-{k}">{_esc(_day_label(k))} ({n})</button>'
        )
    nav = "\n  ".join(nav)

    parts: list[str] = []
    parts.append(f"""<!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Oferty pracy w Przemyślu — dla kobiety</title>
<style>
  :root {{
    --pink: #d63384;
    --pink-soft: #fce4f0;
    --bg: #faf7f9;
    --card: #ffffff;
    --text: #2b2b2b;
    --muted: #777;
    --border: #eee;
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0;
    font-family: "Segoe UI", system-ui, -apple-system, sans-serif;
    background: var(--bg);
    color: var(--text);
    line-height: 1.5;
  }}
  header {{
    background: linear-gradient(135deg, var(--pink), #a21caf);
    color: #fff;
    padding: 2.2rem 1.5rem 1.8rem;
    text-align: center;
  }}
  header h1 {{ margin: 0 0 .4rem; font-size: 1.7rem; }}
  header p {{ margin: 0; opacity: .9; font-size: .95rem; }}
  nav {{
    display: flex;
    flex-wrap: wrap;
    gap: .5rem;
    justify-content: center;
    padding: 1rem;
    background: var(--card);
    border-bottom: 1px solid var(--border);
    position: sticky;
    top: 0;
    z-index: 10;
  }}
  nav .tab {{
    text-decoration: none;
    color: var(--pink);
    background: var(--pink-soft);
    border: none;
    font-family: inherit;
    cursor: pointer;
    padding: .35rem .8rem;
    border-radius: 999px;
    font-size: .85rem;
    font-weight: 600;
  }}
  nav .tab.active {{
    background: linear-gradient(135deg, var(--pink), #a21caf);
    color: #fff;
  }}
  .tab-panel {{ display: none; }}
  .tab-panel.active {{ display: block; }}
  main {{ max-width: 1100px; margin: 0 auto; padding: 1.5rem 1rem 3rem; }}
  section {{ margin-bottom: 2.5rem; }}
  h2 {{
    font-size: 1.25rem;
    color: var(--pink);
    border-left: 5px solid var(--pink);
    padding-left: .6rem;
    margin-bottom: 1rem;
  }}
  #nowe h2 {{ background: var(--pink-soft); border-radius: 0 8px 8px 0; padding: .5rem .6rem; }}
  .count {{ font-size: .85rem; color: var(--muted); font-weight: 600; }}
  .gap {{
    margin: 1.4rem 0 .7rem;
    padding-top: .9rem;
    border-top: 2px dashed var(--border);
    text-align: center;
    color: var(--muted);
    font-size: .8rem;
    font-style: italic;
  }}
  .table-wrap {{
    overflow-x: auto;
    background: var(--card);
    border-radius: 12px;
    box-shadow: 0 2px 10px rgba(0,0,0,.06);
  }}
  table {{ border-collapse: collapse; width: 100%; font-size: .9rem; }}
  thead {{ background: var(--pink-soft); }}
  th {{
    text-align: left;
    padding: .75rem .8rem;
    color: #7b1048;
    font-size: .8rem;
    text-transform: uppercase;
    letter-spacing: .03em;
  }}
  td {{ padding: .7rem .8rem; border-top: 1px solid var(--border); vertical-align: top; }}
  tbody tr:hover {{ background: #fff5fa; }}
  .pay {{ font-weight: 700; color: var(--pink); white-space: nowrap; }}
  .pay.none {{ font-weight: 400; color: var(--muted); }}
  .date {{ white-space: nowrap; font-size: .85rem; }}
  .date.none {{ color: var(--muted); }}
  .link a {{
    color: var(--pink);
    font-weight: 600;
    text-decoration: none;
    border-bottom: 1px dotted var(--pink);
    word-break: break-all;
  }}
  .link a:hover {{ background: var(--pink-soft); }}
  .note {{
    background: #fff8e6;
    border-left: 4px solid #eab308;
    padding: .7rem 1rem;
    border-radius: 0 8px 8px 0;
    font-size: .85rem;
    color: #71580a;
    margin-top: 1rem;
  }}
  .empty {{
    color: var(--muted);
    font-size: .9rem;
    padding: .8rem;
  }}
  footer {{
    text-align: center;
    font-size: .8rem;
    color: var(--muted);
    padding: 1.5rem;
    border-top: 1px solid var(--border);
  }}
  @media (max-width: 700px) {{
    table {{ font-size: .82rem; }}
    th, td {{ padding: .5rem .5rem; }}
  }}
</style>
</head>
<body>

<header>
  <h1>Oferty pracy w Przemyślu</h1>
  <p>Pełna lista direct-linków dla kobiety · bez prac biurowych, budżetówki, państwówki i administracji · {today}</p>
</header>

<nav>
{nav}
</nav>

<main>
""")

    parts.append('<section id="nowe" class="tab-panel active">\n')
    parts.append(
        f'  <h2>Nowe oferty <span class="count">({len(new_items)})</span></h2>\n'
    )
    today_iso = date.today().isoformat()

    def _day(d: dict) -> str:
        return (d.get("posted_at") or d.get("first_seen_at") or "")[:10]

    fresh = [d for d in new_items if _day(d) == today_iso]
    older = [d for d in new_items if _day(d) != today_iso]
    if fresh:
        parts.append(_table(fresh, ""))
    if older:
        if fresh:
            parts.append(
                f'  <p class="gap">starsze niż dzisiaj '
                f"({len(older)}) — z ostatnich 3 dni</p>\n"
            )
        parts.append(_table(older, ""))
    if not fresh and not older:
        parts.append(_table(new_items, "Brak nowych ofert w ostatnich 3 dniach."))
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
            parts.append(_table(items, ""))
            parts.append("  </section>\n")
        parts.append("</div>\n\n")

    parts.append(f"""</main>

<footer>
  Zebrane {today} · {total} ofert · wszystkie linki prowadzą bezpośrednio do ogłoszenia<br>
  Wyłączone: praca biurowa, budżetówka, państwówka, administracja, urzędy miast
</footer>

<script>
  document.querySelectorAll('.tab').forEach(function (b) {{
    b.addEventListener('click', function () {{
      document.querySelectorAll('.tab').forEach(function (x) {{ x.classList.remove('active'); }});
      document.querySelectorAll('.tab-panel').forEach(function (p) {{ p.classList.remove('active'); }});
      b.classList.add('active');
      document.getElementById(b.dataset.t).classList.add('active');
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
