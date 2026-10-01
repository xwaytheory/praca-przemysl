import re
from urllib.parse import urljoin

from fetch import get, get_browser
from scrapers.base import clean, deadline_from, h_id, post_date, register, salary_from


@register("olx")
def scrape_olx() -> list[dict]:
    html = get_browser("https://www.olx.pl/praca/przemysl/")
    jobs = []
    # karta: <a data-testid="card-title-link" href="..."><h4>TYTUL</h4></a>
    for m in re.finditer(
        r'<a[^>]+data-testid="card-title-link"[^>]+href="([^"]+)"[^>]*>\s*<h4[^>]*>(.*?)</h4>',
        html,
        re.S,
    ):
        path, title = m.group(1), clean(re.sub("<[^>]+>", "", m.group(2)))
        if "/oferta/" not in path:
            continue
        url = urljoin("https://www.olx.pl", path.split("?")[0])
        idm = re.search(r"-ID(\w+)\.html", url)
        if not idm:
            continue
        # firma: najblizszy link z olx.pl/home/ po tytule
        tail = html[m.end() : m.end() + 2500]
        comp_m = re.search(r'href="https://[^"]+\.olx\.pl/home/"[^>]*>([^<]+)<', tail)
        company = clean(comp_m.group(1)) if comp_m else ""
        # miasto z href czesto brak — szukamy "Przemysl" w tyle karty
        city_m = re.search(r">\s*(Przemyśl[^<]{0,30})\s*<", tail)
        wide = html[m.end() : m.end() + 6000]
        date_m = re.search(r"card-date-favorite-wrapper[^>]*>", wide)
        posted = post_date(wide[date_m.end() : date_m.end() + 400]) if date_m else ""
        jobs.append(
            {
                "external_id": idm.group(1),
                "title": title,
                "company": company,
                "city": clean(city_m.group(1)) if city_m else "Przemyśl",
                "url": url,
                "salary_raw": salary_from(title, tail[:500]),
                "posted_at": posted,
                "deadline": deadline_from(wide),
            }
        )
    return jobs


@register("pracuj")
def scrape_pracuj() -> list[dict]:
    html = get_browser("https://www.pracuj.pl/praca/przemysl;wp")
    jobs = []
    seen = set()
    # href="https://www.pracuj.pl/praca/slug-miasto,oferta,123..." title="Zobacz ofertę X"
    for m in re.finditer(
        r'href="(https://www\.pracuj\.pl/praca/([^",]+),oferta,(\d+)[^"]*)"[^>]*title="Zobacz ofertę\s*([^"]*)"',
        html,
    ):
        url, slug, oid, title = m.group(1), m.group(2), m.group(3), clean(m.group(4))
        if oid in seen:
            continue
        seen.add(oid)
        # miasto z ogona sluga (np. ...-przemysl, ...-jaroslaw)
        city = ""
        for c in ("przemysl", "przemyśl", "medyka", "orly", "borek", "jaroslaw", "lubaczow"):
            if slug.endswith(c) or f"-{c}" in slug or slug.endswith(c.replace("s", "ś")):
                city = c
                break
        if city and city not in ("przemysl", "przemyśl", "medyka", "orly", "borek"):
            continue  #inne miasto — wylaczamy z monitora Przemyśla
        # firma: employer name w tyle karty (inny link niz oferta)
        tail = html[m.end() : m.end() + 3500]
        comp_m = re.search(r'>([A-ZŻŹĆŁÓŚŃĂĘ][^<]{3,70}(?:Sp\.|S\.A\.|z o\.o|GmbH|LLC)[^<]{0,30})<', tail)
        jobs.append(
            {
                "external_id": oid,
                "title": title,
                "company": clean(comp_m.group(1)) if comp_m else "",
                "city": "Przemyśl",
                "url": url.split("?")[0],
                "salary_raw": salary_from(tail[:800]),
                "posted_at": post_date(tail),
                "deadline": deadline_from(tail),
            }
        )
    if not jobs:
        for m in re.finditer(
            r'href="(https://www\.pracuj\.pl/praca/([^",]+),oferta,(\d+))"',
            html,
        ):
            url, slug, oid = m.group(1), m.group(2), m.group(3)
            if oid in seen:
                continue
            if not slug.endswith("przemysl") and "-przemysl" not in slug:
                continue
            seen.add(oid)
            jobs.append(
                {
                    "external_id": oid,
                    "title": clean(slug.replace("-", " ")),
                    "company": "",
                    "city": "Przemyśl",
                    "url": url,
                    "salary_raw": "",
                }
            )
    return jobs


@register("gowork")
def scrape_gowork() -> list[dict]:
    html = get("https://www.gowork.pl/praca/przemysl;l")
    jobs = []
    # kazdy link oferty: href + najblizszy tekst tytulu <!--]--> ... <!--[
    for m in re.finditer(r'href="(/oferta/([^"]+),([^",]+),przemysl)"', html):
        href, slug, oid = m.group(1), m.group(2), m.group(3)
        # tytul: po href az do <!--]-->TEKSCIK<!--[
        window = html[m.end() : m.end() + 800]
        tm = re.search(r"<!--\[-->\s*([^<]{3,120}?)\s*<!--\]-->", window)
        if not tm:
            tm = re.search(r"<!--\]-->\s*([^<]{3,120}?)\s*<!--", window)
        title = clean(tm.group(1)) if tm else clean(slug.replace("-", " ").replace("+", " "))
        # firma: alt z g-job-item przed tym hrefem (szukamy w oknie wstecz)
        back = html[max(0, m.start() - 2500) : m.start()]
        alt_m = re.findall(r'alt="([^"]+)"', back)
        company = clean(alt_m[-1]) if alt_m else ""
        if title.startswith("/oferta") or len(title) < 3:
            continue
        jobs.append(
            {
                "external_id": oid,
                "title": title,
                "company": company,
                "city": "Przemyśl",
                "url": "https://www.gowork.pl" + href,
                "salary_raw": salary_from(html[m.start() : m.end() + 1500]),
            }
        )
    return jobs


@register("egospodarka")
def scrape_egospodarka() -> list[dict]:
    html = get("https://www.praca.egospodarka.pl/oferty-pracy/m,przemy%C5%9Bl.html")
    jobs = []
    for m in re.finditer(
        r'<div class="oferta">\s*<h3>\s*<a href="([^"]+)" class="search_result_url">([^<]+)</a>[\s\S]{0,400}?'
        r'<span class="dat">([^<]*)</span>[\s\S]{0,200}?'
        r'<span class="prac"><a href="[^"]*">([^<]*)</a>',
        html,
    ):
        url, title, date, company = m.group(1), clean(m.group(2)), clean(m.group(3)), clean(m.group(4))
        id_m = re.search(r",(\d+)\.html", url)
        jobs.append(
            {
                "external_id": id_m.group(1) if id_m else h_id(url),
                "title": title,
                "company": company,
                "city": "Przemyśl",
                "url": urljoin("https://www.praca.egospodarka.pl", url),
                "salary_raw": "",
                "posted_at": post_date(date),
            }
        )
    # fallback prostszy
    if not jobs:
        for m in re.finditer(r'<h3>\s*<a href="(/oferty-pracy/przemysl/[^"]+)" class="search_result_url">([^<]+)</a>', html):
            url, title = m.group(1), clean(m.group(2))
            id_m = re.search(r",(\d+)\.html", url)
            jobs.append(
                {
                    "external_id": id_m.group(1) if id_m else h_id(url),
                    "title": title,
                    "company": "",
                    "city": "Przemyśl",
                    "url": urljoin("https://www.praca.egospodarka.pl", url),
                    "salary_raw": "",
                }
            )
    return jobs


@register("infopraca")
def scrape_infopraca() -> list[dict]:
    html = get_browser("https://www.infopraca.pl/praca?lc=Przemy%C5%9Bl")
    jobs = []
    for m in re.finditer(
        r'data-job-card-job-offer-id-value="(\d+)"[\s\S]{0,1200}?'
        r'<a class="job-card__title-link" href="([^"]+)">([^<]+)</a>[\s\S]{0,400}?'
        r'(?:alt="([^"]*)")?',
        html,
    ):
        oid, path, title, logo = m.group(1), m.group(2), clean(m.group(3)), clean(m.group(4) or "")
        # alt logo jest PRZED tytulem w DOM — wiec firma z osobnego poszukiwania
        jobs.append(
            {
                "external_id": oid,
                "title": title,
                "company": logo,
                "city": "Przemyśl",
                "url": urljoin("https://www.infopraca.pl", path),
                "salary_raw": "",
            }
        )
    # popraw firmy: alt z article przed tytulem
    for block in re.split(r'<article class="job-card"', html)[1:]:
        id_m = re.search(r'data-job-card-job-offer-id-value="(\d+)"', block)
        if not id_m:
            continue
        oid = id_m.group(1)
        alt_m = re.search(r'<img[^>]+alt="([^"]+)"', block)
        for j in jobs:
            if j["external_id"] == oid and alt_m:
                j["company"] = clean(alt_m.group(1))
    return jobs


@register("pracapl")
def scrape_pracapl() -> list[dict]:
    from config import PRACAPL_KEYWORDS

    jobs: list[dict] = []
    seen: set[str] = set()
    for kw in PRACAPL_KEYWORDS:
        url = f"https://www.praca.pl/s-{kw}_m-przemysl.html"
        try:
            html = get(url)
        except Exception:
            continue
        # parsuj po blokach listing__item (lokalizacja musi byc w tym samym bloku)
        for block in re.split(r'<li class="listing__item', html)[1:]:
            block = block[:5000]
            tm = re.search(
                r'<a class="listing__title" href="([^"]+)" data-id="(\d+)" title="([^"]*)"',
                block,
            )
            if not tm:
                continue
            path, oid, title = tm.group(1), tm.group(2), clean(tm.group(3))
            if oid in seen:
                continue
            seen.add(oid)

            # miasto: location-name albo zwyczajny <span>Miasto</span> po firmie
            loc_m = re.search(r'<span class="listing__location-name">\s*([^<]+)', block)
            if not loc_m:
                loc_m = re.search(r'listing__employer-name[\s\S]{0,400}?<span>([^<]*Przemy[^<]*)</span>', block, re.I)
            if not loc_m:
                loc_m = re.search(r'listing__employer-name[\s\S]{0,400}?<span>([^<]{2,40})</span>', block)
            if not loc_m:
                continue
            city = clean(loc_m.group(1))

            # relokacja: cel zagraniczny / spoza Przemyśla → podmieniamy city (filtr odrzuci)
            rm = re.search(
                r'listing__relocation-text">[\s\S]*?</span>\s*</span>\s*([^<\n]+)',
                block,
            )
            if rm:
                dest = clean(rm.group(1))
                if dest and "przemy" not in dest.lower():
                    city = dest

            if "przemysl" not in city.lower() and "przemyśl" not in city.lower():
                continue

            comp_m = re.search(r'class="listing__employer-name"[^>]*>([^<]+)<', block)
            jobs.append(
                {
                    "external_id": oid,
                    "title": title,
                    "company": clean(comp_m.group(1)) if comp_m else "",
                    "city": city,
                    "url": path.split("#")[0],
                    "salary_raw": salary_from(block),
                    "posted_at": post_date(block),
                    "deadline": deadline_from(block),
                }
            )
    return jobs


@register("nuzle")
def scrape_nuzle() -> list[dict]:
    import base64
    import urllib.parse as up

    html = get("https://www.nuzle.pl/przemysl.html")
    jobs = []
    # bloki z data-url (base64) + tytul w h2 span.alike
    for m in re.finditer(r'data-id="([^"]+)"\s+data-url="([^"]+)"([\s\S]{0,1500})', html):
        did, b64, block = m.group(1), m.group(2), m.group(3)
        try:
            pad = "=" * (-len(b64) % 4)
            url = base64.b64decode(b64 + pad).decode()
        except Exception:
            continue
        title_m = re.search(r'<h2><span class="alike">([^<]+)', block)
        if not title_m:
            continue
        jobs.append(
            {
                "external_id": did,
                "title": clean(title_m.group(1)),
                "company": "",
                "city": "Przemyśl",
                "url": url,
                "salary_raw": salary_from(block),
                "posted_at": post_date(block),
            }
        )
    # organiczne: hrefy ...slug,g123456
    for m in re.finditer(r'href="(https://www\.nuzle\.pl/[^"]+,g\d+)"[^>]*>([^<]{5,90})', html):
        url, title = m.group(1), clean(m.group(2))
        oid_m = re.search(r",(g\d+)$", url)
        if not oid_m or any(j["external_id"] == oid_m.group(1) for j in jobs):
            continue
        jobs.append(
            {
                "external_id": oid_m.group(1),
                "title": title,
                "company": "",
                "city": "Przemyśl",
                "url": url,
                "salary_raw": "",
            }
        )
    return jobs


@register("przemyslpraca")
def scrape_przemyslpraca() -> list[dict]:
    html = get("https://przemyslpraca.pl/")
    jobs = []
    for m in re.finditer(
        r'class="announcementItem"[\s\S]{0,900}?<a href="(/announcements/show/(\d+)/[^"]+)"[\s\S]{0,500}?'
        r'alt="([^"]*)"[\s\S]{0,400}?<h3[^>]*>([^<]*)</h3>',
        html,
    ):
        path, oid, alt, h3 = m.group(1), m.group(2), clean(m.group(3)), clean(m.group(4))
        title = h3 or alt
        jobs.append(
            {
                "external_id": oid,
                "title": title,
                "company": "",
                "city": "Przemyśl",
                "url": "https://przemyslpraca.pl" + path,
                "salary_raw": "",
            }
        )
    if not jobs:
        for m in re.finditer(r'<a href="(/announcements/show/(\d+)/[^"]+)">[\s\S]{0,400}?alt="([^"]*)"', html):
            path, oid, alt = m.group(1), m.group(2), clean(m.group(3))
            jobs.append(
                {
                    "external_id": oid,
                    "title": alt,
                    "company": "",
                    "city": "Przemyśl",
                    "url": "https://przemyslpraca.pl" + path,
                    "salary_raw": "",
                }
            )
    return jobs


@register("ogloszeniaprz")
def scrape_ogloszeniaprz() -> list[dict]:
    html = get("https://ogloszeniaprzemysl.pl/ogloszenia/praca/")
    jobs = []
    seen = set()
    for m in re.finditer(r'<a href="(https://ogloszeniaprzemysl\.pl/oferta/[^"]+)" title="([^"]*)"', html):
        url, title = m.group(1), clean(m.group(2))
        if url in seen or not title:
            continue
        seen.add(url)
        slug = url.rstrip("/").split("/")[-1]
        jobs.append(
            {
                "external_id": h_id(url),
                "title": title,
                "company": "",
                "city": "Przemyśl",
                "url": url,
                "salary_raw": "",
            }
        )
        _ = slug
    return jobs


@register("kariera")
def scrape_kariera() -> list[dict]:
    """Strony karier: Biedronka (SF) + FIBRIS + HENSFORT."""
    jobs: list[dict] = []

    # --- Biedronka (SuccessFactors, stabilne hrefy /job/) ---
    try:
        html = get(
            "https://careers.jeronimomartins.com/Biedronka/search/?locale=pl_PL&location=Przemysl"
        )
        for m in re.finditer(
            r'<a[^>]+href="(/Biedronka/job/[^"]+)"[^>]*class="jobTitle-link"[^>]*>([^<]+)</a>',
            html,
        ):
            path, title = m.group(1), clean(m.group(2))
            oid_m = re.search(r"/(\d+)/$", path)
            jobs.append(
                {
                    "external_id": f"biedronka:{oid_m.group(1) if oid_m else h_id(path)}",
                    "title": title,
                    "company": "Biedronka",
                    "city": "Przemyśl",
                    "url": urljoin("https://careers.jeronimomartins.com", path),
                    "salary_raw": "",
                }
            )
    except Exception:
        pass

    # --- FIBRIS ---
    try:
        html = get("https://fibris.pl/pl/pracuj-u-nas")
        for m in re.finditer(
            r'<a href="(/pl/pracuj-u-nas/(\d+)-[^"]+)"[^>]*>\s*([^<]{5,100})\s*</a>',
            html,
        ):
            path, oid, title = m.group(1), m.group(2), clean(m.group(3))
            if any(k in title.lower() for k in ("ksieg", "referent", "biur")):
                continue
            jobs.append(
                {
                    "external_id": f"fibris:{oid}",
                    "title": title,
                    "company": "FIBRIS",
                    "city": "Przemyśl",
                    "url": "https://fibris.pl" + path,
                    "salary_raw": "",
                }
            )
    except Exception:
        pass

    # --- HENSFORT ---
    try:
        html = get("https://hensfort.pl/kariera")
        for m in re.finditer(
            r'<a href="(/kariera/[^"]+)" class="title">([^<]+)</a>[\s\S]{0,300}?'
            r'<p[^>]*>\s*Miejsce pracy,?\s*([^<]*)</p>',
            html,
        ):
            path, title, where = m.group(1), clean(m.group(2)), clean(m.group(3))
            if "przemysl" not in where.lower() and "przemyśl" not in where.lower():
                if "polska" not in where.lower():
                    continue
            jobs.append(
                {
                    "external_id": f"hensfort:{h_id(path)}",
                    "title": title,
                    "company": "HENSFORT",
                    "city": "Przemyśl",
                    "url": "https://hensfort.pl" + path,
                    "salary_raw": "",
                }
            )
        # fallback bez Miejsce pracy
        if not any(j["external_id"].startswith("hensfort:") for j in jobs):
            for m in re.finditer(r'<a href="(/kariera/[^"]+)" class="title">([^<]+)</a>', html):
                path, title = m.group(1), clean(m.group(2))
                if any(k in title.lower() for k in ("czech", "slowac", "niemc", "kierownik", "technolog")):
                    continue
                jobs.append(
                    {
                        "external_id": f"hensfort:{h_id(path)}",
                        "title": title,
                        "company": "HENSFORT",
                        "city": "Przemyśl",
                        "url": "https://hensfort.pl" + path,
                        "salary_raw": "",
                    }
                )
    except Exception:
        pass

    return jobs


@register("rocketjobs")
def scrape_rocketjobs() -> list[dict]:
    """Rocketjobs (Next.js): oferty siedza w escaped JSON w payloadzie strony.
    Jedyne zrodlo, ktore podaje realne widełki + date publikacji."""
    import json
    from datetime import datetime

    base = "https://rocketjobs.pl/oferty-pracy/przemysl"
    jobs: list[dict] = []
    seen: set[str] = set()
    units = {"month": "mies.", "hour": "godz.", "day": "dzien", "year": "rok"}

    def offers(html: str) -> list[dict]:
        m = re.search(r'\\"offers\\":\[', html)
        if not m:
            return []
        start = m.end() - 1
        depth = 0
        for j in range(start, len(html)):
            if html[j] == "[":
                depth += 1
            elif html[j] == "]":
                depth -= 1
                if depth == 0:
                    raw = html[start : j + 1].replace('\\"', '"').replace("\\\\", "\\")
                    try:
                        return json.loads(raw)
                    except Exception:
                        return []
        return []

    for page in (1, 2, 3):
        html = get(base if page == 1 else f"{base}?page={page}")
        rows = offers(html)
        if not rows:
            break
        for o in rows:
            slug = o.get("slug") or ""
            url = f"https://rocketjobs.pl/oferta-pracy/{slug}" if slug else ""
            if not url or url in seen:
                continue
            seen.add(url)
            title = clean(o.get("body") or o.get("title") or "")
            if not title:
                continue
            pay = ""
            for et in o.get("employmentTypes") or []:
                if et.get("currencySource") != "original":
                    continue  # konwersja USD wlasna - nie pokazujemy
                lo, hi = et.get("from"), et.get("to")
                if lo is None and hi is None:
                    continue
                unit = units.get(et.get("unit") or "", "")
                cur = et.get("currency") or "zł"
                if lo is not None and hi is not None and lo != hi:
                    pay = f"{lo:,.0f}–{hi:,.0f} {cur}".replace(",", " ") + (f"/{unit}" if unit else "")
                elif lo is not None:
                    pay = f"od {lo:,.0f} {cur}".replace(",", " ") + (f"/{unit}" if unit else "")
                else:
                    pay = f"do {hi:,.0f} {cur}".replace(",", " ") + (f"/{unit}" if unit else "")
                if et.get("gross"):
                    pay += " brutto"
                break
            posted = ""
            raw = o.get("publishedAt") or o.get("lastPublishedAt") or ""
            if raw:
                try:
                    posted = datetime.fromisoformat(str(raw).replace("Z", "+00:00")).date().isoformat()
                except Exception:
                    posted = str(raw)[:10]
            deadline = ""
            if o.get("expiredAt"):
                deadline = str(o["expiredAt"])[:10]
            jobs.append(
                {
                    "external_id": o.get("guid") or h_id(url),
                    "title": title,
                    "company": clean(o.get("companyName") or ""),
                    "city": clean(o.get("city") or "Przemyśl"),
                    "url": url,
                    "salary_raw": pay,
                    "posted_at": posted,
                    "deadline": deadline,
                }
            )
    return jobs


@register("manual")
def scrape_manual() -> list[dict]:
    """Oferty wklejone recznie do monitor/data/manual.txt (np. z grup Facebook, z
    praca.pl, z ogloszeniaprzemysl.pl). Tamtego serwisu nie da sie skanowac, wiec
    wklejasz sam.

    Akceptowane formaty jednej linii (od najprostszego):
      https://link-do-ogloszenia
      Tytul | https://link-do-ogloszenia
      Tytul | Firma | https://link-do-ogloszenia | widełki
    """
    import os
    from datetime import date

    path = os.path.join(os.path.dirname(__file__), "..", "data", "manual.txt")
    if not os.path.exists(path):
        return []
    jobs: list[dict] = []
    for line in open(path, encoding="utf-8").read().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split("|")]
        url = ""
        for p in reversed(parts):
            if p.startswith("http"):
                url = p
                break
        pay = parts[3] if len(parts) > 3 and not parts[3].startswith("http") else ""
        rest = [p for p in parts[: parts.index(url)] if p] if url else [p for p in parts if p]
        if not rest:
            # sam link -> tytul z ostatniego segmentu sluga
            slug = url.rstrip("/").split("/")[-1].split("?")[0]
            slug = re.sub(r",?oferta,\d+$", "", slug, flags=re.I)  # praca.pl: slug,oferta,ID
            slug = re.sub(r"\.\w{2,5}$", "", slug)
            title = re.sub(r"[-_+]+", " ", slug).strip()
            rest = [title]
        title = rest[0]
        company = rest[1] if len(rest) > 1 else ""
        if not title:
            continue
        jobs.append(
            {
                "external_id": "manual:" + h_id(title + "|" + company),
                "title": title,
                "company": company,
                "city": "Przemyśl",
                "url": url,
                "salary_raw": pay,
                "posted_at": date.today().isoformat(),
                "deadline": "",
            }
        )
    return jobs
