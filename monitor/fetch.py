import time

import requests

UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)
HEADERS = {
    "User-Agent": UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "pl-PL,pl;q=0.9,en;q=0.8",
}

_last: dict[str, float] = {}


def get(url: str, timeout: float = 25.0) -> str:
    """GET przez requests + odstep od domeny."""
    _throttle(url)
    r = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
    r.raise_for_status()
    return r.text


def get_browser(url: str, timeout: float = 30.0) -> str:
    """GET z impersonacja Chrome (curl_cffi) — OLX/Pracuj/infopraca maja antybota."""
    from curl_cffi import requests as creq

    _throttle(url)
    for attempt in range(3):
        r = creq.get(url, impersonate="chrome", timeout=timeout)
        if r.status_code == 200:
            return r.text
        time.sleep(1.5 * (attempt + 1))
    r.raise_for_status()
    return r.text


def _throttle(url: str) -> None:
    from urllib.parse import urlparse

    host = urlparse(url).netloc
    now = time.time()
    delta = now - _last.get(host, 0)
    wait = 2.0 - delta
    if wait > 0:
        time.sleep(wait)
    _last[host] = time.time()
