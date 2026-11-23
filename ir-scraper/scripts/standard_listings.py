"""Parse reports and pagination locally from standard Firecrawl output."""

import re
from datetime import date
from html import unescape
from urllib.parse import parse_qs, urljoin, urlsplit

from bs4 import BeautifulSoup

from espi_listings import (
    DATE_PARTS, PARSERS, PUBLIC_LISTINGS, REPORT_NUMBER, TIME,
    _numeric_date, _polish_date, _report, parse_archive_page, parse_public_page,
)


MARKDOWN_LINK = re.compile(r'\[([^\]\n]+)\]\(([^\s)]+)(?:\s+"[^"\n]*")?\)')
REPORT_HEADING = re.compile(
    rf"^(?:Raport\s+bieżący\s+|RB\s+)?(?:nr[.\s]+)?({REPORT_NUMBER}(?:K\d*)?)$",
    re.I,
)
ORLEN_HEADING = re.compile(rf"^(?:Nr\s+)?({REPORT_NUMBER}(?:K\d*)?)\s*(?={DATE_PARTS})", re.I)
PGE_HEADING = re.compile(rf"^RB\s+nr\s+({REPORT_NUMBER}(?:K\d*)?)\s*[•|–—-]*\s*", re.I)
STAMP_PREFIX = re.compile(rf"^\s*(?:{DATE_PARTS}|\d{{4}}-\d{{2}}-\d{{2}})(?:[\s–—-]*{TIME})?\s*")
PERIODIC_TITLE = re.compile(
    r"\braport(?:y|u)?\s+(?:(?:finansowy|skonsolidowany)\s+)?(?:roczn|kwartaln|półroczn)"
    r"|\braport\s+skonsolidowany\b|\bsprawozdani\w+\s+(?:finansow\w+|z płatności)"
    r"|\b(?:raport|sprawozdanie)\s+(?:za\s+)?(?:[IVX1-4]+\s+)?(?:kwartał|półrocze|20\d{2})"
    r"|\b(?:wyniki finansowe\s+)?(?:QSr?|PSr?|SRR?|RR)\s*(?:\d\s*)?/\s*20\d{2}",
    re.I,
)
PERIODIC_TARGET = re.compile(
    r"\.(?:pdf|zip|xhtml|xlsx?|xml)(?:$|[?#])|/download/|/pr/\d+|"
    r"/raporty-okresowe/(?!raporty-okresowe-\d{4}/?$)(?!\d+\.html(?:$|[?]))[^/?]+",
    re.I,
)
NO_RESULTS = re.compile(
    r"\b(?:brak\s+(?:wyników|raportów|komunikatów)|nie\s+znaleziono\s+(?:wyników|raportów|komunikatów)"
    r"|nie\s+ma\s+(?:wyników|raportów|komunikatów))\b",
    re.I,
)
NEXT = re.compile(r"^(?:następn[aeiy]|dalej|next(?: page)?|[>›»→]+)(?:\s+strona)?$", re.I)
MORE = {"czytaj więcej", "więcej", "pobierz", "pobierz pdf", "pdf", "szczegóły"}


def _stamp(text):
    iso = re.search(r"\b\d{4}-\d{2}-\d{2}\b", text)
    numeric = re.search(DATE_PARTS, text)
    polish = re.search(r"(\d{1,2})\s+([a-ząćęłńóśźż]+)\s+(\d{4})", text, re.I)
    if iso:
        value = date.fromisoformat(iso[0])
    elif numeric:
        value = _numeric_date(*numeric.groups())
    elif polish:
        try:
            value = _polish_date(*polish.groups())
        except KeyError:
            return None, ""
    else:
        return None, ""
    hour = re.search(TIME, text)
    return value, hour[0] if hour else ""


def _text(tag):
    return tag.get_text(" ", strip=True)


def _listing_link(url, target):
    if not target or target.startswith("#"):
        return None
    resolved = urljoin(url, unescape(target.strip("<>")))
    return resolved if urlsplit(resolved).scheme in {"http", "https"} else None


def _rows_from_markdown(url, markdown, ticker):
    for line in markdown.splitlines():
        links = list(MARKDOWN_LINK.finditer(line))
        if not links:
            continue
        if ticker == "LWB":
            link = links[0]
            target = _listing_link(url, link[2])
            day, hour = _stamp(line[:link.start()])
            if target and day and "/wiadomosc/LW-BOGDANKA-S-A-" in urlsplit(target).path:
                yield _report("", day, link[1], target, hour)
        elif ticker == "JSW" and (heading := REPORT_HEADING.fullmatch(links[0][1].strip("* "))):
            first = links[0]
            for title in links[1:]:
                if title[2] == first[2]:
                    target = _listing_link(url, title[2])
                    day, hour = _stamp(line[first.end():title.start()])
                    if target and day:
                        yield _report(heading[1], day, title[1].strip("* "), target, hour)
                    break


def _issuer_card(number, remainder, link, label=""):
    stamp = STAMP_PREFIX.match(remainder)
    if not stamp:
        return None
    day, hour = _stamp(stamp[0])
    title = remainder[stamp.end():].strip().removesuffix(label).strip()
    if title and day:
        return _report(number, day, title, link, hour)
    return None


def _rows_from_html(url, page, ticker):
    for link in page.find_all("a", href=True):
        label = _text(link)
        target = _listing_link(url, link["href"])
        if not label or not target:
            continue
        if ticker == "PGE" and (head := PGE_HEADING.match(label)):
            if row := _issuer_card(head[1], label[head.end():], target):
                yield row
                continue
        if ticker == "PKN" and label.lower() in MORE and re.search(r"/raporty-biezace/\d{4}/", target):
            for block in list(link.parents)[:4]:
                text = _text(block)
                if head := ORLEN_HEADING.match(text):
                    if row := _issuer_card(head[1], text[head.end():], target, label):
                        yield row
                        break
            continue
        lwb = ticker == "LWB" and "/wiadomosc/LW-BOGDANKA-S-A-" in urlsplit(target).path
        heading = REPORT_HEADING.fullmatch(label)
        if not lwb and not heading:
            continue
        for block in list(link.parents)[:4]:
            body = _text(block)
            if len(body) > 900:
                break
            day, hour = _stamp(body)
            if not day:
                continue
            title = label if lwb else next(
                (_text(other) for other in block.find_all("a", href=True)
                 if _listing_link(url, other["href"]) == target and _text(other)
                 and _text(other).lower() not in MORE and not REPORT_HEADING.fullmatch(_text(other))),
                "",
            )
            if not title and heading:
                tail = body[body.find(label) + len(label):]
                tail = STAMP_PREFIX.sub("", tail.lstrip(" –—-")).strip()
                if tail and tail.lower() not in MORE:
                    title = tail
            if title:
                yield _report(heading[1] if heading else "", day, title, target, hour)
                break


def _periodic_row(url, label, target, context):
    resolved = _listing_link(url, target)
    if not resolved or not PERIODIC_TARGET.search(resolved):
        return None
    if not PERIODIC_TITLE.search(label):
        return None
    day, hour = _stamp(context)
    if day:
        return _report("", day, label, resolved, hour)
    return {"numer": "", "data": "", "godzina": "", "tytul": label, "url": resolved}


def _periodic_rows(url, page, markdown):
    if page:
        for link in page.find_all("a", href=True):
            label = _text(link)
            row = link.find_parent("tr")
            context = _text(row) if row else label
            if row := _periodic_row(url, label, link["href"], context):
                yield row
    for line in markdown.splitlines():
        for match in MARKDOWN_LINK.finditer(line):
            if row := _periodic_row(url, match[1].strip("* "), match[2], line):
                yield row


def _pagination(url, page, markdown):
    original = urlsplit(url)
    current_query = parse_qs(original.query)
    current = current_query.get("pageNumber", current_query.get("page", ["1"]))[0]
    zep_listing = original.hostname == "ri.zepak.com.pl"
    original_path = re.sub(r"/\d+\.html$", ".html", original.path) if zep_listing else original.path
    navigation = []
    if page:
        for link in page.select("a[href], link[rel~=next][href]"):
            label = link.get("aria-label") or _text(link) or link.get("title", "")
            rel = link.get("rel", [])
            classes = link.get("class", [])
            navigation.append((label, link["href"], "next" in rel or "next" in classes))
    navigation.extend((entry[1], entry[2], False) for entry in MARKDOWN_LINK.finditer(markdown))
    pages = set()
    next_url = None
    numbered = {}
    for label, href, explicit_next in navigation:
        resolved = _listing_link(url, href)
        if not resolved or resolved == url:
            continue
        target = urlsplit(resolved)
        if target.hostname != original.hostname:
            continue
        if zep_listing:
            target_page = re.search(r"/(\d+)\.html$", target.path)
            target_path = re.sub(r"/\d+\.html$", ".html", target.path)
            if target_path != original_path or parse_qs(target.query).get("y") != current_query.get("y"):
                continue
            if target_page:
                pages.add(int(target_page[1]))
        elif target.path != original_path or not target.query:
            continue
        if explicit_next or NEXT.fullmatch(label.strip()):
            next_url = next_url or resolved
        if label.isdigit():
            pages.add(int(label))
            numbered[int(label)] = resolved
    if zep_listing:
        return {"total_sub_pages": max(pages, default=1), "next_page_url": next_url}
    if not next_url:
        current_page = next((values[0] for key, values in current_query.items() if key.endswith("[currentPage]")), current)
        page_number = int(current_page) if current_page.isdigit() else 1
        next_url = numbered.get(page_number + 1)
    return {"total_pages": max(pages, default=None), "next_page_url": next_url}


def parse_standard_listing(url, payload, ticker, report_type):
    """Read publisher rows from cached Markdown / HTML, without another request."""
    markdown = payload.get("markdown") or ""
    html = payload.get("html") or ""
    page = BeautifulSoup(html, "html.parser") if html else None
    if report_type == "okresowe":
        rows = list(_periodic_rows(url, page, markdown))
        if ticker == "LWB":
            rows = [row for row in _rows_from_markdown(url, markdown, ticker) if PERIODIC_TITLE.search(row["tytul"])]
            if not rows and page:
                rows = [row for row in _rows_from_html(url, page, ticker) if PERIODIC_TITLE.search(row["tytul"])]
    else:
        rows = parse_public_page(ticker, url, html) if html and ticker in PUBLIC_LISTINGS else []
        if not rows and markdown and ticker in PARSERS:
            rows = parse_archive_page(ticker, url, markdown)
        if not rows and markdown and ticker in {"LWB", "JSW"}:
            rows = list(_rows_from_markdown(url, markdown, ticker))
        if not rows and page:
            rows = list(_rows_from_html(url, page, ticker))
    if not rows and not NO_RESULTS.search(markdown or (_text(page) if page else "")):
        raise ValueError(f"{ticker}: nie udało się rozpoznać układu wykazu {url}; surowa odpowiedź pozostaje w cache.")
    unique = {}
    for row in rows:
        key = tuple(row[field] for field in ("numer", "tytul", "url"))
        previous = unique.get(key)
        if (previous is None or (not previous["data"] and row["data"])):
            unique[key] = row
        elif previous["data"] != row["data"] and row["data"]:
            unique[(*key, row["data"])] = row
    return {"raporty": list(unique.values()), **_pagination(url, page, markdown)}
