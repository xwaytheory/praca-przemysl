#!/usr/bin/env python3
"""Monitor pracy w Przemyślu — skan + index.html (dla kobiety, bez biura/budżetówki).

Usage:  python monitor/run.py [--warmup] [--source olx] [--db PATH]
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from config import SOURCES  # noqa: E402
from filters import passes  # noqa: E402
from scrapers import sources as _sources  # noqa: F401,E402  (rejestracja)
from scrapers.base import REGISTRY  # noqa: E402
import render  # noqa: E402
import store  # noqa: E402

# Portale z ogloszeniami prywatnymi nie podaja firmy — etykieta zamiast pustej kolumny
DEFAULT_COMPANY = {
    "olx": "Osoba prywatna",
    "nuzle": "Osoba prywatna",
    "przemyslpraca": "Osoba prywatna",
    "ogloszeniaprz": "Osoba prywatna",
}


def main() -> int:
    ap = argparse.ArgumentParser(description="Skan ofert pracy w Przemyślu → index.html")
    ap.add_argument("--warmup", action="store_true", help="pierwszy skan: bez listy w konsoli, ale HTML tak")
    ap.add_argument("--source", action="append", help="tylko wybrane zrodlo (np. olx); mozliwe wielokrotnie")
    ap.add_argument("--db", default=None, help="sciezka do SQLite")
    ap.add_argument("--all", action="store_true", help="pokaz tez oferty spoza bialej listy (diagnostyka)")
    ap.add_argument("--no-html", action="store_true", help="nie generuj index.html")
    args = ap.parse_args()

    names = args.source or list(SOURCES)
    unknown = [n for n in names if n not in REGISTRY]
    if unknown:
        print(f"Nieznane zrodla: {', '.join(unknown)}. Dostepne: {', '.join(REGISTRY)}")
        return 2

    con = store.open_db(args.db)
    prev_scan = store.get_meta(con, "last_scan_at")
    print(f"Skanuję {len(names)} źródeł: {', '.join(names)}")
    if prev_scan:
        print(f"Poprzedni skan: {prev_scan} (sekcja 'Nowe' obejmie wszystko od niego)\n")
    else:
        print()

    total_fetched = total_kept = total_new = 0
    errors: list[str] = []
    new_rows: list = []
    rejected_diag: list[tuple[str, str, str]] = []

    for name in names:
        fn = REGISTRY[name]
        try:
            jobs = fn()
        except Exception as e:
            errors.append(f"{name}: {type(e).__name__}: {e}")
            print(f"  [BŁĄD] {name:16} {e}")
            continue

        kept = []
        present = []
        for job in jobs:
            ok, why = passes(job)
            if ok:
                kept.append(job)
                present.append(job["external_id"])
            else:
                if args.all:
                    rejected_diag.append((name, job.get("title", "")[:60], why))

        new = 0
        for job in kept:
            if not job.get("company"):
                job["company"] = DEFAULT_COMPANY.get(name, "Pracodawca nie podany")
            if store.upsert(con, name, job):
                new += 1
        store.mark_missed(con, name, present)
        con.commit()

        total_fetched += len(jobs)
        total_kept += len(kept)
        total_new += new
        print(f"  [ok   ] {name:16} pobrane={len(jobs):4}  po filtrach={len(kept):4}  nowe={new:4}")

    # --- drugi brak na liscie -> sprawdzamy link, dopiero potem "expired" ---
    dead = store.dead_candidates(con)
    if dead:
        revived = killed = 0
        for job in dead:
            if store.probe_alive(job["url"]):
                store.touch(con, job["source"], job["external_id"])
                revived += 1
            else:
                store.expire(con, job["source"], job["external_id"])
                killed += 1
        con.commit()
        print(
            f"  [weryfikacja] podejrzane o znikniecie: {len(dead)} | "
            f"nadal zyje (zostaje na stronie): {revived} | faktycznie wygasle: {killed}"
        )
        print()

    new_rows = store.new_jobs(con)
    print()
    if errors:
        print("Błędy źródeł:")
        for e in errors:
            print(f"  - {e}")
        print()

    print(f"RAZEM: pobrane={total_fetched}  po filtrach={total_kept}  nowych w DB={total_new}")

    # --- index.html: zawsze pełna lista aktywnych ofert ---
    if not args.no_html:
        active = store.active_jobs(con)
        recent_ids = {
            (r["source"], r["external_id"])
            for r in store.recent_jobs(con, since=prev_scan)
        }
        out = render.render(
            active,
            recent_ids=recent_ids,
            scan_at=store.get_meta(con, "last_scan_at") or "",
        )
        print(f"HTML: {out}  ({len(active)} ofert, {len(recent_ids)} nowych)")

    store.set_meta_now(con, "last_scan_at")

    if args.warmup:
        store.mark_notified(con)
        print("Warmup — zapisano stan. Kolejne uruchomienie pokaże tylko nowe oferty w konsoli.")
        con.close()
        return 0

    if not new_rows:
        print("\nBrak nowych ofert od ostatniego skanu (index.html i tak odświeżony).")
        if args.all and rejected_diag:
            print(f"\n--- odrzucone ({len(rejected_diag)}) ---")
            for src, title, why in rejected_diag[:40]:
                print(f"  [{src}] {title}  → {why}")
        con.close()
        return 0

    print(f"\n=== NOWE OFERTY ({len(new_rows)}) ===\n")
    by_src: dict[str, list] = {}
    for r in new_rows:
        by_src.setdefault(r["source"], []).append(r)

    for src, rows in by_src.items():
        print(f"── {src} ({len(rows)}) " + "─" * 40)
        for r in rows:
            salary = f"  |  {r['salary_raw']}" if r["salary_raw"] else ""
            company = f"  — {r['company']}" if r["company"] else ""
            print(f"  • {r['title']}{company}{salary}")
            if r["url"]:
                print(f"    {r['url']}")
        print()

    if args.all and rejected_diag:
        print(f"\n--- odrzucone ({len(rejected_diag)}) ---")
        for src, title, why in rejected_diag[:40]:
            print(f"  [{src}] {title}  → {why}")
        if len(rejected_diag) > 40:
            print(f"  ... i {len(rejected_diag) - 40} więcej")

    store.mark_notified(con)
    con.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
