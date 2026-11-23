"""Extract the substantive ESPI disclosure and source evidence from a cached page."""

import re
from datetime import date, datetime
from html import unescape
from urllib.parse import unquote, urljoin, urlsplit
from zoneinfo import ZoneInfo

from bs4 import BeautifulSoup, Comment, NavigableString


DAY = r"(?:\d{4}-\d{2}-\d{2}|\d{1,2}[.\-/]\d{1,2}[.\-/]\d{4})"
CLOCK = r"(?:[01]?\d|2[0-3]):[0-5]\d(?::[0-5]\d)?"
DAY_TIME = re.compile(rf"\b(?P<day>{DAY})(?:[ ,|/T]+(?P<clock>{CLOCK}))?\b")
CLOCK_ONLY = re.compile(rf"(?<!\d)({CLOCK})(?!\d)")
REPORT = r"\d{1,4}\s*[/\-]\s*(?:19|20)\d{2}(?:\s*[/\-]?\s*K(?:\d+)?\b)?"
REFERENCE_NUMBER = re.compile(rf"(?<![\d/.]){REPORT}(?![\d/])", re.I)
REPORT_HEADING = re.compile(
    rf"(?:^\s*\|?\s*(?:raport\s+bieżący|regulatory announcement|current report)\b"
    rf"(?:\s*\(ESPI\)|\s+z plikiem)?\s*(?:nr\.?|no\.?)?\s*:?[ \t]*"
    rf"|^\s*(?:raport\s+)?(?:nr\.?|numer raportu)\s*:?\s*|(?<=\())({REPORT})",
    re.I,
)
REPORT_STEM = r"rapor(?:t\w*|ci\w*)"
REPORT_REF = re.compile(
    rf"\b(?:{REPORT_STEM}\s+(?:bieżąc\w*\s+|ESPI\s+)?(?:nr\.?\s*)?|RB\s*(?:nr\.?\s*)?)"
    rf"({REPORT}(?:\s*(?:,|;|\bi\b|\boraz\b)\s*{REPORT})*)",
    re.I,
)
REPORT_REF_CONTINUATION = re.compile(
    rf"\b(?:{REPORT_STEM}\s+bieżąc\w*|{REPORT_STEM}\s+ESPI)\b"
    rf"[^.\n]{{0,100}}?\bnr\.?\s*({REPORT}[^.\n)]{{0,260}})",
    re.I,
)
ISSUER_PREFIX = re.compile(r"^[A-ZĄĆĘŁŃÓŚŹŻ0-9 .,\"-]{2,85}\($")
LINK = re.compile(r"\[([^\]\n]+)\]\((<[^>]+>|[^\s)]+)(?:\s+\"[^\"]*\")?\)")
CONTENT = re.compile(
    r"^(?:treść\s+(?:raportu|informacji|komunikatu|korekty|korygowanego raportu)|report content|content of the report)"
    r"(?:\s*:\s*(.*))?\s*$",
    re.I,
)
BARE_DAY = re.compile(rf"^(?:data\s*(?:publikacji|sporządzenia\s+raportu)?\s*:?\s*)?{DAY}(?:\s*(?:r\.?|[|,])?\s*{CLOCK})?(?:\s+r\.?)?$", re.I)
PUBLISH_LABEL = re.compile(r"^(?:data(?:\s+i\s+godzina)?\s+publikacji|opublikowano|publication date|published)\b", re.I)
REFERENCE_STOP = re.compile(
    r"^(?:drukuj(?: stronę)?|wydrukuj stronę|wróć(?: do listy)?|powrót(?: do listy)?|zobacz więcej raportów"
    r"|zobacz\s+również|najnowsze raporty|pozostałe z kategorii|skontaktuj się"
    r"|więcej na\s*:|kom espi zdz\b|nazwa arkusza:|copyright\b|\[Go Back\])",
    re.I,
)
ATTACHMENT_LABEL = re.compile(r"^(?:pliki do pobrania|załączniki(?: raportu)?|pobierz (?:materiał|raport)|attachments?)\s*:?$", re.I)
PDF_PATH = re.compile(r"\.pdf(?:[.,/?#]|$)|/download/attachment/|/(?:media/\d+/)?download/[^?#]*\.pdf", re.I)
REPORT_PATH = re.compile(r"/(?:pr/\d+|[^/?]*raport[^/?]*|komunikaty-espi|komunikat(?:y)?-spolek)(?:[/?]|$)", re.I)
PDF_ONLY = re.compile(
    r"(?:\b(?:treść|szczegół\w*|pełn\w*)\s+(?:raport\w*|komunikat\w*)\s+"
    r"(?:(?:jest\s+)?dostępn\w*\s+|znajduje się\s+|został\w*\s+zamieszczon\w*\s+)?w\s+załącznik\w*\b"
    r"|\btreść\s+(?:raport\w*|komunikat\w*)\s+stanowi\s+załącznik\b"
    r"|\b(?:raport|raport bieżący|treść)\s+w\s+załączeniu\b"
    r"|\bprzekazuje\s+w\s+załączeniu\s+treść\s+(?:raport\w*|komunikat\w*)\b"
    r"|\bpowyższ\w*\s+informacj\w*\s+przekazuj\w*\s+w\s+załącznik\w*\b)",
    re.I,
)
BLOCKED = re.compile(
    r"request rejected|access denied|just a moment|cloudflare challenge|captcha|api security challenge"
    r"|nietypow[ąa]\s+komunikacj|dzia[łl]anie zosta[łl]o odrzucone|your request has been blocked",
    re.I,
)
MONTHS = dict(zip(
    ("stycznia", "lutego", "marca", "kwietnia", "maja", "czerwca", "lipca", "sierpnia",
     "września", "października", "listopada", "grudnia"),
    range(1, 13),
))
WRITTEN_DAY = re.compile(r"\b(\d{1,2})\s+(" + "|".join(MONTHS) + r")\s+(\d{4})\b", re.I)
BLOCK_NAMES = {
    "address", "article", "blockquote", "dd", "div", "dl", "dt", "figcaption", "h1", "h2", "h3", "h4",
    "h5", "header", "li", "main", "p", "section", "table", "td", "th", "tr",
}
ISSUER_SELECTORS = {
    "ENA": (".publication__content--report", ".report-publication", "article.publication"),
    "PKN": ("main .report-detail", "main article", "main", ".root"),
    "PGE": ("main .report-details", "main article", "main", "#content"),
    "TPE": (".newsfull .report", ".container--report + main .report", "main .report", "main"),
    "UNT": (".container-article .article-content", ".article-content", "main article"),
    "ZEP": (".content-container .content", "main .content", "main"),
}


def tidy(value):
    return " ".join(unescape(value).replace("\u200b", "").split())


def format_report(number):
    formatted = re.sub(r"\s+", "", number).upper().replace("-", "/")
    return re.sub(r"(?<=\d)K(?=\d*$)", "/K", formatted)


def parse_stamp(value):
    value = tidy(value)
    try:
        if re.match(r"^\d{4}-\d{2}-\d{2}T", value):
            dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if dt.tzinfo is not None:
                dt = dt.astimezone(ZoneInfo("Europe/Warsaw"))
            return dt.date().isoformat(), dt.strftime("%H:%M")
    except ValueError:
        pass
    if found := DAY_TIME.search(value):
        for style in ("%Y-%m-%d", "%d.%m.%Y", "%d-%m-%Y", "%d/%m/%Y"):
            try:
                day = datetime.strptime(found["day"], style).date().isoformat()
                return day, clean_clock(found["clock"])
            except ValueError:
                continue
    if written := WRITTEN_DAY.search(value):
        try:
            day = date(int(written[3]), MONTHS[written[2].lower()], int(written[1])).isoformat()
        except ValueError:
            return "", ""
        current = CLOCK_ONLY.search(value[written.end():])
        return day, clean_clock(current[1] if current else "")
    return "", ""


def clean_clock(value):
    if not value:
        return ""
    hour, minute, *_ = value.split(":")
    result = f"{int(hour):02d}:{minute}"
    return "" if result == "00:00" else result


def html_lines(node):
    parts = []

    def visit(element):
        if isinstance(element, Comment):
            return
        if isinstance(element, NavigableString):
            text = tidy(str(element))
            if text:
                parts.extend((text, " "))
            return
        tag = element.name
        if tag in {"br", "hr"}:
            parts.append("\n")
            return
        if tag in BLOCK_NAMES:
            parts.append("\n")
        for child in element.children:
            visit(child)
        if tag in BLOCK_NAMES:
            parts.append("\n")

    visit(node)
    return [line.strip() for line in "".join(parts).splitlines() if line.strip()]


def markdown_lines(markdown):
    lines = []
    in_fence = False
    for raw in markdown.splitlines():
        if raw.strip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        value = LINK.sub(r"\1", raw)
        value = re.sub(r"^(?:\s*[>#]+\s*|\s*[-*+]\s+)", "", value)
        value = tidy(value.strip(" *_"))
        if value and re.search(r"\w", value):
            lines.append(value)
    return lines


def find_report_header(lines, expected):
    fallback = None
    for i, line in enumerate(lines):
        match = REPORT_HEADING.search(line)
        if match is not None and match.start() and not ISSUER_PREFIX.fullmatch(line[:match.start()]):
            match = None
        if match is None and re.fullmatch(REPORT, line) and (
            (i > 0 and lines[i - 1].casefold().strip(" :") in {"numer raportu", "report number", "nr raportu"})
            or expected and format_report(line) == expected
        ):
            match = re.match(rf"({REPORT})", line, re.I)
        if not match or len(line) > 280:
            continue
        if fallback is None:
            fallback = (i, match)
        if not expected or format_report(match[1]) == expected:
            return i, match
    return fallback or (-1, None)


def extract_body(lines, header, scoped, ticker, external, headings, content_limit=18):
    start = max(0, header + 1)
    if header < 0 and not scoped:
        return "", 0
    first = lines[start:start + content_limit + 1]
    for i, line in enumerate(first):
        if match := CONTENT.match(line):
            start += i + 1
            prefix = [match[1]] if match[1] else []
            break
    else:
        prefix = []
        if header < 0 and ticker == "TPE" and not external and first:
            start += 1
    result = prefix
    stop = len(lines)
    for i in range(start, len(lines)):
        line = lines[i]
        if REFERENCE_STOP.match(line) or ATTACHMENT_LABEL.fullmatch(line):
            stop = i
            if result or ATTACHMENT_LABEL.fullmatch(line) or i > start + 8:
                break
            continue
        if i < start + 9 and (
            BARE_DAY.fullmatch(line) or PUBLISH_LABEL.match(line) or line.casefold() in headings or re.match(
                r"^(?:numer raportu|tytuł raportu|data\s*:|data sporządzenia raportu|podstawa prawna|temat\s*:)", line, re.I
            ) or re.match(r"^(?:art\.\s+\d|§\s*\d)", line, re.I) and not result
            or re.match(r"^\d{2}\.\d{2}\.\d{4}[, ].*aktualizacja", line, re.I)
        ):
            continue
        if len(line) < 12 and re.fullmatch(r"(?:ESPI|RB|[| .–—-]+)", line, re.I):
            continue
        result.append(line)
    return "\n\n".join(result), stop


def resolve_link(url, href):
    if href is None or href.startswith(("#", "mailto:", "tel:")):
        return ""
    if urlsplit(url).hostname in {"gpw.pl", "www.gpw.pl"} and href.startswith("attachment/"):
        # GPW applies this same mapping to the attachment links in the public report view.
        return f"https://espiebi.pap.pl/espi/pl/reports/view/{href}"
    target = urljoin(url, unescape(href.strip("<> ")))
    return target if urlsplit(target).scheme in {"http", "https"} and target != url else ""


def page_links(url, node, markdown):
    for link in node.select("a[href], iframe[src], object[data], embed[src]") if node else ():
        href = link.get("href") or link.get("src") or link.get("data")
        label = tidy(link.get_text(" ", strip=True) or link.get("title") or link.get("aria-label") or "")
        if target := resolve_link(url, href):
            yield target, label
    for link in LINK.finditer(markdown):
        if target := resolve_link(url, link[2]):
            yield target, tidy(link[1])


def collect_links(url, node, markdown, lines, body, stop, scoped):
    attachments = {}
    reports = {}
    visible = "\n".join(lines[max(0, stop - 5):stop + 24]).casefold()
    for target, label in page_links(url, node, markdown):
        looks_pdf = PDF_PATH.search(unquote(target)) or re.search(r"\bPDF\b", label, re.I)
        if looks_pdf and (scoped or not label or label.casefold() in body.casefold() or label.casefold() in visible):
            attachments.setdefault(target, {"url": target, "title": label or unquote(urlsplit(target).path.rsplit("/", 1)[-1])})
        elif label and REPORT_PATH.search(urlsplit(target).path) and label.casefold() in body.casefold():
            reports.setdefault(target, {"url": target, "title": label})
    return list(attachments.values()), list(reports.values())


def extract_references(text, expected):
    matches = (match[1] for pattern in (REPORT_REF, REPORT_REF_CONTINUATION) for match in pattern.finditer(text))
    numbers = (format_report(number[0]) for part in matches for number in REFERENCE_NUMBER.finditer(part))
    return list(dict.fromkeys(number for number in numbers if number != expected))


def timestamp_from_page(soup, node, lines, header, report_match, ticker, external, host, expected_date, expected):
    if host in {"gpw.pl", "www.gpw.pl"} and node and node.parent:
        element = node.parent.select_one("span.date")
        if element is not None:
            label = tidy(element.get_text(" ", strip=True))
            match = re.search(rf"\|\s*ESPI\s*\|\s*({REPORT})", label, re.I)
            if match and (not expected or format_report(match[1]) == expected):
                return parse_stamp(label)
    if ticker == "ENA" and not external and node:
        element = node.select_one(".publication__details time[datetime], .publication-list__details-time[datetime]")
        if element is not None:
            return parse_stamp(element["datetime"])
    if not external and ticker == "UNT" and node:
        element = node.find_previous(["h1"])
        if element is not None and element.parent and "container-article" in element.parent.get("class", []):
            for item in element.parent.select("time[datetime]"):
                if item.find_parent(class_="container-article") is element.parent:
                    day, clock = parse_stamp(item["datetime"])
                    if day and (not expected_date or day == expected_date):
                        return day, clock
    local = lines[max(0, header - 4):max(0, header) + 12]
    header_text = lines[header] if header >= 0 else ""
    if external and host.endswith(("gpw.pl", "gpwinfostrefa.pl", "biznes.pap.pl")):
        for line in lines[max(0, header - 55):max(0, header) + 5]:
            if re.match(DAY, line) and re.search(r"\|\s*ESPI\s*\|", line, re.I):
                day, clock = parse_stamp(line)
                line_number = re.search(rf"\|\s*ESPI\s*\|\s*({REPORT})", line, re.I)
                if clock and line_number and (not expected or format_report(line_number[1]) == expected):
                    return day, clock
    if report_match and not external and ticker in {"PKN", "UNT", "ZEP"}:
        trailer = header_text[report_match.end():]
        day, clock = parse_stamp(trailer)
        if ticker == "UNT" and not clock and (found := CLOCK_ONLY.match(trailer.strip("| "))) is not None:
            clock = clean_clock(found[1])
        if day or clock:
            return day, clock
    for i, line in enumerate(local):
        if not PUBLISH_LABEL.match(line):
            continue
        combined = line + " " + (local[i + 1] if i + 1 < len(local) else "")
        day, clock = parse_stamp(combined)
        if day:
            if external and ("pap-mediaroom.pl" in host or not re.search(r"\bESPI\b", line, re.I)
                             and not host.endswith(("gpw.pl", "gpwinfostrefa.pl", "parkiet.com"))):
                return day, ""
            return day, clock
    for line in local:
        if BARE_DAY.fullmatch(line):
            day, clock = parse_stamp(line)
            if day:
                return day, clock if ticker in {"PKN", "ENA", "TPE", "UNT", "ZEP"} and not external else ""
        if external and "pap-mediaroom.pl" in host and "aktualizacja" in line.lower():
            return parse_stamp(line)[0], ""
    if soup and external and host.endswith(("gpw.pl", "gpwinfostrefa.pl")):
        element = soup.select_one("time[datetime]")
        if element is not None:
            return parse_stamp(element["datetime"])
    return "", ""


def parse_detail(url, payload, ticker, report_number="", expected_date=""):
    """Return the document text, publication evidence and report/attachment links."""
    markdown = payload.get("markdown") or ""
    html = payload.get("html") or ""
    host = urlsplit(url).hostname or ""
    expected = format_report(report_number)
    output = {"text": "", "publication_date": expected_date, "publication_date_source": "catalog" if expected_date else "",
              "publication_time": "", "time_source_url": "", "reported_number": "",
              "attachments": [], "report_links": [], "reference_numbers": [], "status": "unrecognized"}
    if PDF_PATH.search(unquote(urlsplit(url).path)):
        return {**output, "attachments": [{"url": url, "title": unquote(urlsplit(url).path.rsplit("/", 1)[-1])}],
                "status": "pdf_required", "document_url": url}

    http_status = payload.get("provenance", {}).get("http_status")
    if http_status in {401, 403, 429} or BLOCKED.search((markdown[:1500] + html[:1500])):
        return {**output, "status": "blocked"}
    if http_status and http_status >= 400:
        return {**output, "status": f"http_{http_status}"}
    external = any(host.endswith(site) for site in ("pap-mediaroom.pl", "pap.pl", "gpw.pl", "gpwinfostrefa.pl", "parkiet.com"))
    official_gpw = host in {"gpw.pl", "www.gpw.pl"}
    if official_gpw:
        selectors = (".report-data", "main article", "main")
    elif external:
        selectors = ("article.node--type-article .node__content", "article .node__content", ".article-content",
                     'article [itemprop="articleBody"]', "main article", "article", "main")
    else:
        selectors = ISSUER_SELECTORS.get(ticker, ("main article", "main"))
    soup = BeautifulSoup(html, "html.parser") if html else None
    node = None
    if soup:
        for item in soup.select("script, style, noscript, nav, footer, aside, template, [aria-hidden='true']"):
            item.decompose()
        node = next((item for sel in selectors if (item := soup.select_one(sel)) is not None), None)
    raw = html_lines(node) if node else []
    precise_scope = bool(node and node.name != "main" and (external or ticker not in {"PKN", "PGE"}))
    headings = {tidy(tag.get_text(" ", strip=True)).casefold() for tag in soup.select("h1, h2") if tag} if soup else set()
    header, match = find_report_header(raw, expected)
    if official_gpw and not any(CONTENT.match(line) for line in raw):
        body, stop = "", 0
    else:
        body, stop = extract_body(raw, header, precise_scope, ticker, external, headings, content_limit=70 if official_gpw else 18)
    md = markdown_lines(markdown)
    md_header, md_match = find_report_header(md, expected)
    md_headings = {tidy(LINK.sub(r"\1", item[1])).casefold() for item in re.finditer(r"^#{1,2}\s+(.+)$", markdown, re.M)}
    md_body, md_stop = extract_body(md, md_header, False, ticker, external, md_headings)
    if not md_body and node is None and any(CONTENT.match(line) for line in md[:35]):
        md_body, md_stop = extract_body(md, md_header, True, ticker, external, md_headings)
    if not body or len(body) < 75 and len(md_body) > len(body):
        raw, header, match, body, stop = md, md_header, md_match, md_body, md_stop

    stamp = timestamp_from_page(soup, node, raw, header, match, ticker, external, host, expected_date, expected)
    if not all(stamp) and md and raw is not md:
        alternate = timestamp_from_page(soup, None, md, md_header, md_match, ticker, external, host, expected_date, expected)
        if not stamp[0] or not alternate[0] or stamp[0] == alternate[0]:
            stamp = (stamp[0] or alternate[0], stamp[1] or alternate[1])
    if not stamp[0] and external and soup and host.endswith("pap-mediaroom.pl"):
        element = soup.select_one("article > .date")
        if element is not None:
            stamp = parse_stamp(element.get_text(" ", strip=True))[0], ""
    if not match and md_match:
        match = md_match
    if not match and soup:
        _, match = find_report_header([tag.get_text(" ", strip=True) for tag in soup.select("h1")], expected)
    if not match and official_gpw and node:
        element = node.parent.select_one("span.date")
        if element is not None:
            match = re.search(rf"\|\s*ESPI\s*\|\s*({REPORT})", element.get_text(" ", strip=True), re.I)

    link_scope = node
    if external and "pap-mediaroom.pl" in host and soup:
        link_scope = soup.select_one("article.node--type-article") or node
    attachments, report_links = collect_links(url, link_scope, markdown, raw, body, stop, precise_scope)
    if not body and attachments or attachments and len(body) < 300 and PDF_ONLY.search(body):
        status = "pdf_required"
    elif body and (len(body) >= 40 or len(body.split()) >= 5):
        status = "ok"
    else:
        status = "unrecognized"
    if not body and BLOCKED.search((soup.get_text(" ", strip=True) if soup else markdown)[:500]):
        status = "blocked"
    result = {
        **output, "text": body, "publication_date": stamp[0] or expected_date,
        "publication_date_source": "source" if stamp[0] else ("catalog" if expected_date else ""),
        "publication_time": stamp[1], "time_source_url": url if stamp[1] else "",
        "reported_number": format_report(match[1]) if match else "",
        "attachments": attachments, "report_links": report_links,
        "reference_numbers": extract_references(body, expected), "status": status,
    }
    if status == "pdf_required" and len(attachments) == 1:
        result["document_url"] = attachments[0]["url"]
    return result
