"""Persistent cache for public listing URLs fetched through Firecrawl."""

import hashlib
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from tempfile import NamedTemporaryFile
from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit

from filelock import FileLock


class UncertainFetchError(RuntimeError):
    """A previous paid request may have been billed without a stored result."""


class UnbilledFetchError(RuntimeError):
    """The service rejected the request before accepting a billable job."""


def replace_with_retry(source, target):
    """Retry local OneDrive sharing violations without replaying a request."""
    for delay in (0.05, 0.1, 0.2, 0.4, 0.8, 1.6):
        try:
            os.replace(source, target)
            return
        except PermissionError:
            time.sleep(delay)
    os.replace(source, target)


def canonical_url(url):
    parsed = urlsplit(url)
    if parsed.scheme.lower() not in {"http", "https"} or not parsed.hostname or parsed.username is not None:
        raise ValueError("Cache wymaga publicznego adresu HTTP(S).")
    host = parsed.hostname.lower()
    if ":" in host:
        host = f"[{host}]"
    port = parsed.port
    if port and (parsed.scheme.lower(), port) not in {("http", 80), ("https", 443)}:
        host = f"{host}:{port}"
    path = quote(parsed.path or "/", safe="/:@!$&'()*+,;=-._~%")
    path = re.sub(r"%[0-9a-fA-F]{2}", lambda match: match[0].upper(), path)
    parameters = sorted(parse_qsl(parsed.query, keep_blank_values=True), key=lambda pair: pair[0])
    return urlunsplit((parsed.scheme.lower(), host, path, urlencode(parameters), ""))


class FirecrawlCache:
    def __init__(self, root):
        self.root = Path(root)

    def _entry_path(self, key):
        digest = hashlib.sha256(key.encode("utf-8")).hexdigest()
        return self.root / digest[:2] / f"{digest}.json"

    @staticmethod
    def _read(path, key):
        try:
            try:
                text = path.with_suffix(".recovery.json").read_text(encoding="utf-8")
            except FileNotFoundError:
                text = path.read_text(encoding="utf-8")
        except FileNotFoundError:
            return None
        try:
            entry = json.loads(text)
            if entry.get("url") != key:
                raise ValueError("niezgodny URL")
            if entry.get("state") == "complete" and isinstance(entry.get("payload"), dict):
                return entry["payload"]
            if entry.get("state") != "pending":
                raise ValueError("nieznany format wpisu")
        except (ValueError, AttributeError) as exc:
            raise UncertainFetchError(f"Uszkodzony cache dla {key}; sprawdź wpis {path}.") from exc
        raise UncertainFetchError(
            f"Poprzednie zapytanie dla {key} mogło zostać rozliczone; sprawdź wpis {path}."
        )

    @staticmethod
    def _write(path, entry):
        temporary = None
        try:
            with NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as stream:
                temporary = Path(stream.name)
                json.dump(entry, stream, ensure_ascii=False, allow_nan=False)
                stream.flush()
                os.fsync(stream.fileno())
            try:
                replace_with_retry(temporary, path)
            except PermissionError:
                if entry["state"] != "complete":
                    raise
                replace_with_retry(temporary, path.with_suffix(".recovery.json"))
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)

    def get(self, url):
        key = canonical_url(url)
        return self._read(self._entry_path(key), key)

    def put(self, url, payload):
        """Add existing source material with no API call or overwrite."""
        if not isinstance(payload, dict):
            raise TypeError("Wpis cache musi być słownikiem.")
        key = canonical_url(url)
        path = self._entry_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        with FileLock(f"{path}.lock"):
            if self._read(path, key) is not None:
                return False
            self._write(path, {"url": key, "state": "complete", "payload": payload})
            return True

    def reserve_batch(self, urls, reservation):
        reserved = []
        for url in urls:
            key = canonical_url(url)
            path = self._entry_path(key)
            path.parent.mkdir(parents=True, exist_ok=True)
            with FileLock(f"{path}.lock"):
                try:
                    available = self._read(path, key) is None
                except UncertainFetchError:
                    continue
                if available:
                    self._write(path, {"url": key, "state": "pending", "reservation": reservation})
                    reserved.append(key)
        return reserved

    def finish_batch(self, url, reservation, payload=None):
        """Complete or release a reservation only after the batch API confirms its outcome."""
        key = canonical_url(url)
        path = self._entry_path(key)
        with FileLock(f"{path}.lock"):
            entry = json.loads(path.read_text(encoding="utf-8"))
            if entry.get("reservation") != reservation or entry.get("state") != "pending":
                return False
            if path.with_suffix(".recovery.json").is_file():
                return False
            if payload is None:
                path.unlink()
            else:
                self._write(path, {"url": key, "state": "complete", "payload": payload})
            return True

    def get_or_fetch(self, url, fetch):
        """Read a cached page or call fetch once under a durable reservation."""
        key = canonical_url(url)
        path = self._entry_path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        with FileLock(f"{path}.lock"):
            payload = self._read(path, key)
            if payload is not None:
                return payload, True
            requested_at = datetime.now(timezone.utc).isoformat()
            self._write(path, {"url": key, "state": "pending", "requested_at": requested_at})
            try:
                payload = fetch(url)
            except UnbilledFetchError:
                path.unlink()
                raise
            # A failure with unknown billing leaves the reservation in place.
            if not isinstance(payload, dict):
                raise TypeError("Odpowiedź scrape musi być słownikiem.")
            self._write(path, {
                "url": key, "state": "complete", "requested_at": requested_at, "payload": payload,
            })
            return payload, False


_SOURCE = re.compile(r"(?m)^## Źródło strony: (https?://\S+)[ \t]*$")
_SUBPAGE = re.compile(r"(?m)^### Podstrona (\d+)[ \t]*$")
_LINK = re.compile(r"\]\((https?://[^\s)]+)\)")


def _trim_separator(text):
    return re.sub(r"\n\n---\s*\Z", "", text.strip()).strip()


def read_legacy_pages(legacy_json, legacy_md):
    """Pair exact archived listing URLs with retained Markdown and matching report links."""
    legacy_json, legacy_md = Path(legacy_json), Path(legacy_md)
    snapshot = json.loads(legacy_json.read_text(encoding="utf-8-sig"))
    text = legacy_md.read_text(encoding="utf-8-sig")
    sources = {canonical_url(url) for url in snapshot["zrodla"]}
    markers = list(_SOURCE.finditer(text))
    if not markers or not all(canonical_url(match[1]) in sources for match in markers):
        raise ValueError(f"Archiwum Markdown nie zgadza się z listą źródeł w {legacy_json.name}.")

    archived = {}
    for marker, next_marker in zip(markers, [*markers[1:], None]):
        url = canonical_url(marker[1])
        section = _trim_separator(text[marker.end():next_marker.start() if next_marker else len(text)])
        children = list(_SUBPAGE.finditer(section))
        archived[url] = section[:children[0].start()].strip() if children else section
        if not children:
            continue
        parsed = urlsplit(url)
        for child, following in zip(children, [*children[1:], None]):
            path = f"{parsed.path.removesuffix('.html')}/{child[1]}.html"
            child_url = canonical_url(urlunsplit(parsed._replace(path=path)))
            if child_url in sources:
                archived[child_url] = section[child.end():following.start() if following else len(section)].strip()

    reports = {}
    for report in snapshot["raporty"]:
        if report.get("url"):
            reports.setdefault(canonical_url(report["url"]), []).append(report)
    provenance = {
        "provider": "firecrawl_legacy_archive",
        "captured_at": snapshot.get("data_scrapowania"),
        "json": legacy_json.name,
        "markdown": legacy_md.name,
    }
    pages = {}
    for url in sorted(sources):
        markdown = archived.get(url, "")
        links = list(dict.fromkeys(canonical_url(link) for link in _LINK.findall(markdown)))
        pages[url] = {
            "raporty": [report for link in links for report in reports.get(link, ())],
            "markdown": markdown,
            "total_pages": None,
            "total_sub_pages": None,
            "next_page_url": None,
            "provenance": provenance,
        }
    return pages


def seed_legacy_pages(cache, legacy_json, legacy_md):
    return sum(cache.put(url, payload) for url, payload in read_legacy_pages(legacy_json, legacy_md).items())
