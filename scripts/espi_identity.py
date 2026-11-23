"""Shared identity rules for sources listing Polish ESPI disclosures."""

import hashlib
import re
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime
from urllib.parse import parse_qsl, quote, unquote, urlencode, urlsplit, urlunsplit


NUMBER = re.compile(r"(?<!\d)(\d{1,4})\s*[/\-]\s*((?:19|20)\d{2})(?!\d)")
SUFFIX = re.compile(r"\s*[/\-]?\s*(K(?:\s*[-.]?\s*\d+)?|KOREKTA)(?!\w)", re.IGNORECASE)
REPORT_CORRECTION = re.compile(
    r"(?:^|[–—-]\s+)(?:korekta|sprostowanie|uzupełnienie)(?:\s+treści)?\s+raportu\b",
    re.IGNORECASE,
)
CORRECTION_TITLE_PREFIX = re.compile(r"^korekta\s*:", re.IGNORECASE)
NUMBER_CHANNEL = re.compile(r"\b(ESPI|EBI)\b", re.IGNORECASE)


@dataclass(frozen=True, slots=True)
class ReportIdentity:
    report_number: str
    base_number: str
    is_correction: bool = False
    corrects_report_number: str = ""
    correction_suffix: str = ""


def format_number(match):
    return f"{int(match[1])}/{match[2]}" if match else ""


def classify_report(number: str, title: str = "", corrects_number: str = "") -> ReportIdentity:
    number = number.strip()
    title = title.strip()
    match = NUMBER.search(number)
    base = format_number(match)
    verified_reference = format_number(NUMBER.fullmatch(corrects_number.strip()))
    if match and (suffix_match := SUFFIX.match(number, match.end())):
        suffix_digits = re.sub(r"\D", "", suffix_match[1])
        suffix = f"K{int(suffix_digits)}" if suffix_digits else "K"
        return ReportIdentity(f"{base}/{suffix}", base, True, verified_reference or base, suffix)

    correction = REPORT_CORRECTION.search(title)
    if verified_reference or correction or CORRECTION_TITLE_PREFIX.match(title):
        reference = NUMBER.search(title, correction.end()) if correction else None
        corrected = verified_reference or format_number(reference) or base
        if corrected and (not base or corrected == base):
            return ReportIdentity(f"{corrected}/K", corrected, True, corrected, "K")
        return ReportIdentity(base, base, True, corrected)
    return ReportIdentity(base, base)


def report_channel(report) -> str:
    for field in ("kanal", "channel", "system", "numer"):
        match = NUMBER_CHANNEL.search(str(report.get(field) or ""))
        if match:
            return match[1].upper()
    return "ESPI"


def normalize_url(value: str) -> str:
    if not value:
        return ""
    url = urlsplit(value)
    parameters = [(key, val) for key, val in parse_qsl(url.query) if not key.lower().startswith("utm_")]
    return urlunsplit((url.scheme.lower(), url.netloc.lower(), url.path.rstrip("/"), urlencode(sorted(parameters)), ""))


def url_identity(value: str) -> str:
    """Compare publisher links without rewriting the link stored in the record."""
    url = urlsplit(normalize_url(value))
    host = url.netloc.removeprefix("www.")
    if host == "ri.zepak.com.pl" and (record := re.match(r"/pl/raporty/raporty-biezace/(\d+)-", url.path)):
        return f"{host}/pl/raporty/raporty-biezace/{record[1]}"
    if host == "ir.enea.pl" and (record := re.match(r"/pr/(\d+)(?:/|$)", url.path)):
        return f"{host}/pr/{record[1]}"
    path = quote(unicodedata.normalize("NFC", unquote(url.path)), safe="/:@")
    return urlunsplit(("", host, path, url.query, "")).removeprefix("//") if host else ""


def normalized_title(title: str) -> str:
    return " ".join(unicodedata.normalize("NFC", title).casefold().split())


def date_key(value) -> str:
    if isinstance(value, date):
        return value.isoformat()[:10]
    for form in ("%Y-%m-%d", "%d.%m.%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(str(value).strip(), form).date().isoformat()
        except ValueError:
            continue
    return str(value or "").strip()


def numbered_key(ticker: str, number: str) -> str:
    digits, year = number.split("/")
    return f"{ticker}_{year}_{digits}"


def event_key(ticker: str, identity: ReportIdentity, published, url: str, title: str) -> str:
    if identity.base_number:
        base = numbered_key(ticker, identity.base_number)
        suffix = identity.correction_suffix
        if not suffix:
            return base
        if suffix != "K":
            return f"{base}_{suffix}"
        # Generic /K may be used more than once by the same issuer.
        evidence = url_identity(url) or f"{date_key(published)}|{normalized_title(title)}"
        digest = hashlib.sha256(evidence.encode()).hexdigest()[:16]
        return f"{base}_K_{digest}"

    # Preserve the established fallback key for disclosures with no number.
    evidence = normalize_url(url) or f"{date_key(published) or 'invalid_date'}|{normalized_title(title)}"
    digest = hashlib.sha256(evidence.encode()).hexdigest()[:20]
    return f"{ticker}_espi_{digest}"


def deduplicate_reports(reports):
    """Deduplicate repeated listing rows while retaining genuine disagreements."""
    unique = {}
    for report in reports:
        number = str(report.get("numer") or "")
        title = str(report.get("tytul") or "")
        url = str(report.get("url") or "")
        published = date_key(report.get("data"))
        identity = classify_report(number, title)
        key = (
            report_channel(report),
            event_key("", identity, published, url, title),
            published,
            url_identity(url) or normalized_title(title),
        )
        preferred = unique.get(key)
        if preferred is None or (report.get("godzina") and not preferred.get("godzina")):
            unique[key] = report
    return list(unique.values())
