# Monitor pracy w Przemyślu

Jedno uruchomienie = jeden skan + odświeżenie **`index.html`** (pełna lista direct-linków, styl jak przykład — dla kobiety, zero biura/budżetówki/państwówki/administracji).

## Uruchomienie

```bash
pip install -r monitor/requirements.txt   # pierwszy raz
python monitor/run.py                     # skan → konsola (nowe) + index.html
python monitor/run.py --warmup            # pierwszy raz: zapisz stan, HTML tak
python monitor/run.py --source olx        # tylko jedno źródło
python monitor/run.py --all               # diagnostyka: pokaż odrzucone + powód
python monitor/run.py --no-html           # bez generowania HTML
```

Wynik:
- **`index.html`** w root projektu — wszystkie aktywne ofert y z linkami bezpośrednimi (4 sekcje jak w przykładzie).
- SQLite: `monitor/data/jobs.db` — kolejne skany pokazują w konsoli tylko **nowe** oferty.

## Co skanuje (10 źródeł)

| Źródło | Co |
|---|---|
| OLX Praca | `olx.pl/praca/przemysl` |
| Pracuj.pl | `pracuj.pl/praca/przemysl;wp` |
| GoWork | `gowork.pl/praca/przemysl;l` |
| eGospodarka | oferty dla Przemyśla |
| infoPraca | `?lc=Przemyśl` |
| Praca.pl | frazy miastowe z weryfikacją lokalizacji |
| Nuzle | `nuzle.pl/przemysl.html` |
| przemyslpraca.pl | lokalne ogłoszenia |
| ogloszeniaprzemysl.pl | kategoria praca |
| Strony karier | Biedronka (SF), FIBRIS, HENSFORT |

## Filtry (`monitor/config.py`)

1. **Miasto** — Przemyśl i bliska okolica.
2. **EXCLUDE (twarde)** — biuro, administracja, urzędy, budżetówka, państwówka, samorząd, szpital/ szkoły / policja / MZK, zdalna, praca za granicę, `gmbh`.
3. **INCLUDE (biała lista, raczej dla kobiety)** — sprzedaż, sklep, gastronomia, hotele, uroda/farmacja, opieka, sprzątanie, lekka produkcja/magazyn, kurier, sezonowe. Tytuł musi trafić w ≥1 słowo.

Słowa edytujesz w `monitor/config.py` → od razu działa przy następnym skanie.

## HTML

`monitor/render.py` buduje `index.html` w 4 sekcjach (jak przykład):

1. Farmacja, zdrowie, uroda  
2. Sprzedaż, obsługa klienta, handel  
3. Gastronomia, hotelarstwo, usługi  
4. Magazyn, produkcja, opiekun i pozostałe  

Każdy wiersz: stanowisko · pracodawca · płaca · **klikalny direct-link** do ogłoszenia.

## Uwagi

- OLX/Pracuj/infoPraca: `curl_cffi` (antybot) — w `requirements.txt`.
- Throttle 2 s na domenę.
- Padło źródło? `[BŁĄD]` w konsoli, reszta leci dalej — naprawiasz scraper w `monitor/scrapers/sources.py`.
