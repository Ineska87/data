"""Recover structured report rows from archived official IR listing pages."""

import re
from datetime import date
from html import unescape
from pathlib import Path
from urllib.parse import parse_qs, urljoin, urlsplit
from urllib.request import Request, urlopen


ARCHIVE_STEMS = {
    "PKN": "orlen_biezace_1999-2026",
    "PGE": "pge_raporty_biezace_2009-2026",
    "TPE": "tauron_biezace_2010-2026",
    "ENA": "enea_biezace_2005-2026",
    "ZEP": "zepak_biezace_20260625_121028",
    "UNT": "unimot_biezace_2013-2026",
}
START = re.compile(r"^## Źródło strony:\s+(https?://\S+)[ \t]*$", re.M)
ZEP_SUBPAGE = re.compile(r"^### Podstrona (\d+)[ \t]*$", re.M)
REPORT_NUMBER = r"\d{1,4}\s*/\s*\d{4}(?:\s*/\s*(?:K\d*|[A-ZĄĆĘŁŃÓŚŹŻ]+))?"
TIME = r"\d{1,2}:\d{2}"
DATE_PARTS = r"(\d{1,2})[.\-](\d{1,2})[.\-](\d{4})"
MONTHS = dict(
    zip(
        ("sty", "lut", "mar", "kwi", "maj", "cze", "lip", "sie", "wrz", "paź", "lis", "gru"),
        range(1, 13),
    )
)
LINK = re.compile(r"\]\((https?://[^\s)]+)\)")


def _report(number, day, title, link, hour=""):
    return {
        "numer": re.sub(r"\s*/\s*", "/", number.strip()),
        "data": day.isoformat(),
        "godzina": hour.strip(),
        "tytul": " ".join(unescape(title).split()),
        "url": unescape(link),
    }


def _polish_date(day, month, year):
    return date(int(year), MONTHS[month[:3].lower()], int(day))


def _numeric_date(day, month, year):
    return date(int(year), int(month), int(day))


def _clean_lines(text):
    return [value for line in text.splitlines() if (value := line.strip().strip("\\").strip())]


def _segments(text, anchor):
    entries = list(anchor.finditer(text))
    for index, entry in enumerate(entries):
        end = entries[index + 1].start() if index + 1 < len(entries) else len(text)
        yield entry, text[entry.end():end]


def _orlen(text):
    anchor = re.compile(rf"^-\s+(?:Nr\s+)?({REPORT_NUMBER})\s*{DATE_PARTS}[^\n]*$", re.M | re.I)
    for head, body in _segments(text, anchor):
        number, day, month, year = head.groups()
        link = re.search(r"\[Więcej\]\((https?://[^\s)]+)\)", body, re.I)
        headline = _clean_lines(body[:link.start()]) if link else []
        if headline:
            yield _report(number, _numeric_date(day, month, year), headline[0], link[1])


def _pge(text):
    anchor = re.compile(rf"^-\s*\[\s*RB\s+nr\s+({REPORT_NUMBER})[^\n]*$", re.M | re.I)
    for head, body in _segments(text, anchor):
        stamp = re.search(rf"^\s*{DATE_PARTS}\s*({TIME})?", body, re.M)
        link = LINK.search(body, stamp.end()) if stamp else None
        headline = _clean_lines(body[stamp.end():link.start()]) if link else []
        if headline:
            day, month, year, hour = stamp.groups()
            yield _report(head[1], _numeric_date(day, month, year), " ".join(headline), link[1], hour or "")


def _tauron(text):
    anchor = re.compile(
        rf"^\[Raport bieżący nr\s+({REPORT_NUMBER})[^\n\]]*\]\((https?://[^\s)]+)\)\s*$",
        re.M | re.I,
    )
    for head, body in _segments(text, anchor):
        stamp = re.search(rf"^\s*{DATE_PARTS}\s*({TIME})?", body, re.M)
        more = re.search(r"\[Czytaj więcej\]", body[stamp.end():], re.I) if stamp else None
        headline = _clean_lines(body[stamp.end():stamp.end() + more.start()]) if more else []
        if headline:
            day, month, year, hour = stamp.groups()
            yield _report(head[1], _numeric_date(day, month, year), " ".join(headline), head[2], hour or "")


def _enea(text):
    anchor = re.compile(r"^\[(\d{1,2})([a-ząćęłńóśźż]{3})(\d{4})[^\n]*$", re.M | re.I)
    for head, body in _segments(text, anchor):
        number = re.search(rf"Raport bieżący nr\s+({REPORT_NUMBER})", body, re.I)
        if not number:
            continue
        link = LINK.search(body, number.end())
        if not link or "/pr/" not in link[1]:
            continue
        headline = _clean_lines(body[number.end():link.start()])
        hour = re.search(TIME, body[:number.start()])
        if headline:
            yield _report(number[1], _polish_date(*head.groups()), " ".join(headline), link[1], hour[0] if hour else "")


def _unimot(text):
    anchor = re.compile(rf"^Raport bieżący nr\s+({REPORT_NUMBER})[^\n]*$", re.M | re.I)
    for head, body in _segments(text, anchor):
        stamp = re.search(r"^\s*(\d{1,2})\s+([a-ząćęłńóśźż]+)\s+(\d{4})", body, re.M | re.I)
        headline = re.search(r"\[\*\*(.*?)\*\*", body, re.S)
        link = LINK.search(body, headline.end()) if headline else None
        if stamp and link:
            yield _report(head[1], _polish_date(*stamp.groups()), headline[1], link[1])


def _zepak(text):
    row = re.compile(
        rf"^\|\s*({REPORT_NUMBER})\s*\|\s*(\d{{4}}-\d{{2}}-\d{{2}})\s*\|\s*\[([^\n]+?)\]\((https?://[^\s)]+)\)\s*\|",
        re.M | re.I,
    )
    for number, stamp, headline, link in row.findall(text):
        yield _report(number, date.fromisoformat(stamp), headline, link)


PARSERS = {"PKN": _orlen, "PGE": _pge, "TPE": _tauron, "ENA": _enea, "UNT": _unimot, "ZEP": _zepak}


def parse_archive_page(ticker: str, url: str, markdown: str) -> list[dict]:
    """Parse public listing rows from a cached Markdown page."""
    return [entry | {"source_page": url} for entry in PARSERS[ticker](markdown)]


def archived_markdown_pages(data_root: Path, ticker: str):
    """Read whole archived pages, preserving ZE PAK nested page identities."""
    path = data_root / "raw" / "espi" / "archivemd_backup" / f"{ARCHIVE_STEMS[ticker]}.md"
    text = path.read_text(encoding="utf-8-sig")
    for section, body in _segments(text, START):
        url = section[1]
        if ticker != "ZEP":
            yield url, body
            continue
        heading = ZEP_SUBPAGE.search(body)
        yield url, body[:heading.start()] if heading else body
        for subpage, content in _segments(body, ZEP_SUBPAGE):
            suffix = f"/{subpage[1]}.html?"
            yield url.replace(".html?", suffix, 1), content


def load_archived_pages(data_root: Path, ticker: str, start: date, end: date) -> dict:
    """Plan from archived page contents and include date-boundary pages."""
    result = {}
    for url, markdown in archived_markdown_pages(data_root, ticker):
        reports = parse_archive_page(ticker, url, markdown)
        dates = [date.fromisoformat(report["data"]) for report in reports]
        if dates and not (max(dates) < start or min(dates) > end):
            result[url] = {"reports": reports, "markdown": markdown}
    return result


PUBLIC_LISTINGS = {
    "TPE": (
        "https://www.tauron.pl/tauron/relacje-inwestorskie/raporty-biezace?pageSize=15&pageNumber={page}",
        1, 1,
    ),
    "ENA": (
        "https://ir.enea.pl/lista-raportow/kategoria/3611/raporty-bie-ce?pageLimit=50&offset={page}",
        0, 50,
    ),
    "UNT": (
        "https://www.unimot.pl/relacje-inwestorskie/raporty-i-strategia/raporty-biezace?page={page}",
        1, 1,
    ),
    "ZEP": (
        "https://ri.zepak.com.pl/pl/raporty/raporty-biezace.html?y={page}",
        None, None,
    ),
}


def public_html(url):
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Firefox/141.0",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    with urlopen(request, timeout=20) as response:
        return response.read()


def _text(tag):
    return tag.get_text(" ", strip=True)


def _html_row(number_text, stamp, title, href):
    number = re.search(REPORT_NUMBER, number_text, re.I)
    if not number:
        raise ValueError(f"Brak prawidłowego numeru raportu: {number_text!r}")
    iso = re.search(r"\b\d{4}-\d{2}-\d{2}\b", stamp)
    numeric = re.search(DATE_PARTS, stamp)
    if iso:
        day = date.fromisoformat(iso[0])
    elif numeric:
        day = _numeric_date(*numeric.groups())
    else:
        polish = re.search(r"(\d{1,2})\s+([a-ząćęłńóśźż]+)\s+(\d{4})", stamp, re.I)
        if not polish:
            raise ValueError(f"Brak prawidłowej daty publikacji: {stamp!r}")
        day = _polish_date(*polish.groups())
    hour = re.search(TIME, stamp)
    return _report(number[0], day, title, href, hour[0] if hour else "")


def parse_public_page(ticker: str, url: str, html: bytes) -> list[dict]:
    """Parse issuer-hosted HTML without an API call."""
    from bs4 import BeautifulSoup

    page = BeautifulSoup(html, "html.parser")
    rows = []
    if ticker == "ZEP":
        for row in page.select("table tr"):
            fields = row.find_all("td")
            if len(fields) != 3 or not re.fullmatch(REPORT_NUMBER, _text(fields[0]), re.I):
                continue
            link = fields[2].find("a", href=True)
            if link:
                rows.append(_html_row(_text(fields[0]), _text(fields[1]), _text(link), urljoin(url, link["href"])))
    elif ticker == "TPE":
        for card in page.select(".reports__element"):
            link = card.select_one("a.reports__element--header[href]")
            day = card.select_one(".reports__element--info--date")
            title = card.select_one(".reports__element--header--h2")
            if link and day and title:
                rows.append(_html_row(_text(link), _text(day), _text(title), urljoin(url, link["href"])))
    elif ticker == "ENA":
        for card in page.select("a.reportListCurrent-js[href]"):
            stamp = card.select_one("time[datetime]")
            number = card.select_one(".report-list__item-current")
            title = card.select_one(".report-list__item-title")
            if stamp and number and title:
                rows.append(_html_row(_text(number), stamp["datetime"], _text(title), urljoin(url, card["href"])))
    elif ticker == "UNT":
        for title in page.select(".card-article__title"):
            link = title.find_parent("a", href=True)
            stamp = link.find_previous_sibling("p") if link else None
            fields = stamp.find_all("span", recursive=False) if stamp else []
            if len(fields) == 2:
                rows.append(_html_row(_text(fields[0]), _text(fields[1]), _text(title), urljoin(url, link["href"])))
    else:
        raise ValueError(f"Brak selektorów HTML dla {ticker}")
    return [row | {"source_page": url} for row in rows]


def load_public_pages(ticker: str, start: date, end: date, *, fetch=public_html) -> dict:
    """Download public HTML up to the requested year/date boundary, without Firecrawl."""
    template, first_page, page_step = PUBLIC_LISTINGS[ticker]
    pages = {}
    signatures = set()

    def read(url):
        html = fetch(url)
        reports = parse_public_page(ticker, url, html)
        if not reports:
            raise ValueError(f"{ticker}: nie odczytano wierszy listy {url}")
        signature = tuple(report["url"] for report in reports)
        if signature in signatures:
            raise ValueError(f"{ticker}: powtórzona strona listy {url}")
        signatures.add(signature)
        stamps = [date.fromisoformat(report["data"]) for report in reports]
        if max(stamps) >= start and min(stamps) <= end:
            pages[url] = {"reports": reports, "markdown": "", "source": "public_html"}
        return min(stamps), html

    if ticker == "ZEP":
        from bs4 import BeautifulSoup

        for year in range(end.year, start.year - 1, -1):
            url = template.format(page=year)
            while url:
                _, html = read(url)
                next_link = BeautifulSoup(html, "html.parser").select_one("a.next[href*='raporty-biezace']")
                url = urljoin(url, next_link["href"]) if next_link else None
                if url:
                    target = urlsplit(url)
                    if target.hostname != "ri.zepak.com.pl" or parse_qs(target.query).get("y") != [str(year)]:
                        raise ValueError(f"Nieoczekiwana dalsza strona wykazu ZE PAK: {url}")
    else:
        page = first_page
        while read(template.format(page=page))[0] >= start:
            page += page_step
    years = {date.fromisoformat(report["data"]).year for page in pages.values() for report in page["reports"]}
    if not set(range(start.year, end.year + 1)).issubset(years):
        raise ValueError(f"{ticker}: wykaz HTML nie pokrywa całego zakresu {start}–{end}")
    return pages
