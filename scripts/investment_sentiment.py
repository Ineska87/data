"""Prepare the reviewed document, passage, and validation datasets for the study."""

from __future__ import annotations

import base64
from collections import Counter, defaultdict
import hashlib
from io import BytesIO
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
import unicodedata
from zipfile import ZipFile

import numpy as np
import pandas as pd
from lxml import html

from data_paths import DATA_ROOT, load_study_scope

CORPUS = DATA_ROOT / "processed" / "corpus"
SENTIMENT = DATA_ROOT / "processed" / "sentiment"
VALIDATION = SENTIMENT / "validation"
METADATA = DATA_ROOT / "metadata"
REPORTS = DATA_ROOT / "raw" / "reports"
REPORT_MANIFEST = CORPUS / "report_manifest.csv"
PASSAGE_SCORES = SENTIMENT / "investment_passage_scores.parquet"
PUBLICATION_COLUMNS = ["report_id", "publication_date", "published_at", "source_url"]
PASSAGE_COLUMNS = ["document_id", "start_char", "end_char", "project_id", "source_locator"]
POOL_COLUMNS = ["document_id", "start_char", "end_char", "split"]
LABELS = ("negative", "neutral", "positive")
WORD_RE = re.compile(r"[^\W\d_]+", re.UNICODE)
NARRATIVE_TYPES = {"management_report", "management_commentary", "financial_notes", "ceo_letter", "integrated_report"}
CORE_PERIODS = {"Q1", "H1", "Q3", "AR"}
REFERENCE_LIST = REPORTS / "publication_archive" / "event_periodic_references.csv"
INVESTMENT_LANGUAGE = re.compile(
    r"\b(?:inwestycj\w*|nakład\w*|capex|modernizacj\w*|rozbudow\w*|"
    r"harmonogram\w*|dekarbonizacj\w*|budow\w*|projekt\w*)\b", re.I,
)
AR_PACKAGE = re.compile(r"TPE_20(?:20|21|22|23|24|25)_AR_skonsolidowany\.(?:pdf|zip|7z)$", re.I)
BASELINE_ARCHIVE = re.compile(
    r"(?:PKN|TPE)_2019_(?:Q3|AR)_(?:sprawozdanie|skonsolidowany)\.(?:zip|7z|pdf)$", re.I,
)
ORLEN_PILOT_PACKAGES = {
    "PKN_2021_Q1_sprawozdanie.zip",
    "PKN_2023_Q1_sprawozdanie.zip",
    "PKN_2024_Q3_sprawozdanie.zip",
}


def data_relative(path: Path) -> str:
    return path.relative_to(DATA_ROOT).as_posix()


def resolve_data_file(path: str) -> Path:
    relative = str(path).replace("\\", "/").removeprefix("data/")
    candidate = (DATA_ROOT / relative).resolve()
    if not candidate.is_relative_to(DATA_ROOT.resolve()):
        raise ValueError(f"Path outside data: {path}")
    return candidate


def read_input(path: Path, columns: list[str]) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=columns)
    frame = pd.read_csv(path, dtype=str, keep_default_na=False, encoding="utf-8-sig")
    missing = set(columns) - set(frame)
    if missing:
        raise ValueError(f"{path.name}: missing {', '.join(sorted(missing))}")
    return frame


def read_management_archive(path: Path) -> tuple[str, str]:
    """Read the management XHTML directly from an archive, without writing members."""
    def is_management(name: str) -> bool:
        stem = Path(name).name.lower()
        return stem.endswith(".xhtml") and ("sprzarzadu" in stem or "sprawozdaniezarzadu" in stem)

    with path.open("rb") as stream:
        signature = stream.read(6)
    if signature.startswith(b"PK\x03\x04"):
        with ZipFile(path) as archive:
            names = [name for name in archive.namelist() if is_management(name)]
            if len(names) != 1:
                raise ValueError(f"{path.name}: expected one management XHTML, found {len(names)}")
            member = Path(names[0]).name
            xhtml = archive.read(names[0])
    elif signature == b"7z\xbc\xaf\x27\x1c":
        try:
            listing = subprocess.run(["tar", "-tf", str(path)], capture_output=True, check=True)
            basenames = [name.rsplit(b"/", 1)[-1] for name in listing.stdout.splitlines()]
            names = [name.decode("ascii") for name in basenames if name.isascii() and is_management(name.decode("ascii"))]
            if len(names) != 1:
                raise ValueError(f"{path.name}: expected one management XHTML, found {len(names)}")
            member = names[0]
            # Use the unique ASCII basename with libarchive's wildcard handling.
            xhtml = subprocess.run(
                ["tar", "-xOf", str(path), "--", "*"+member],
                capture_output=True, check=True,
            ).stdout
        except (FileNotFoundError, subprocess.CalledProcessError) as error:
            raise RuntimeError("Reading TAURON 7z packages requires bsdtar (libarchive).") from error
    else:
        raise ValueError(f"{path.name}: unsupported annual-report archive")
    text = text_from_xhtml(xhtml)
    if len(text) < 100:
        raise ValueError(f"{path.name}: management XHTML has no usable text")
    return text, member


def text_from_xhtml(xhtml: bytes) -> str:
    page = html.fromstring(xhtml, parser=html.HTMLParser(encoding="utf-8", no_network=True, huge_tree=True))
    for el in page.xpath("//script|//style|//head|//*[name()='ix:header' or name()='ix:hidden']"):
        el.drop_tree()
    blocks = [" ".join(line.split()) for line in page.text_content().splitlines() if line.strip()]
    return "\n".join(blocks)


def read_orlen_archive(path: Path, extract_pdf_text) -> tuple[str, str, str]:
    """Select the principal report from the three verified ORLEN pilot packages."""
    with ZipFile(path) as archive:
        reports = [entry for entry in archive.infolist() if entry.filename.lower().endswith(".pdf")]
        if not reports:
            raise ValueError(f"{path.name}: archive contains no PDF")
        member = max(reports, key=lambda entry: entry.file_size)
        text, _, status = extract_pdf_text(archive.read(member))
    return text, member.filename, status


def read_baseline_archive(path: Path, extract_pdf_text) -> tuple[str, str, str, str]:
    with path.open("rb") as stream:
        signature = stream.read(6)
    if signature.startswith(b"%PDF-"):
        text, _, status = extract_pdf_text(path)
        return text, "", status, "pdf"
    if signature.startswith(b"PK\x03\x04"):
        with ZipFile(path) as archive:
            reports = [member for member in archive.infolist() if member.filename.lower().endswith(".pdf")]
            management = [member for member in reports if re.search(
                r"sprawozdani\w*[-_.\s]*zarz[ąa]du|management[-_.\s]*report", Path(member.filename).name, re.I,
            )]
            if reports:
                selected = max(management or reports, key=lambda member: member.file_size)
                text, _, status = extract_pdf_text(archive.read(selected))
                return text, selected.filename, status, "management_pdf_from_zip" if management else "periodic_report_pdf_from_zip"
    text, member = read_management_archive(path)
    return text, member, "ok", "management_xhtml"


def load_publications(path: Path, id_column="report_id") -> pd.DataFrame:
    columns = [id_column, *PUBLICATION_COLUMNS[1:]]
    rows = read_input(path, columns)[columns]
    if rows[id_column].duplicated().any():
        raise ValueError(f"{path.name}: duplicate {id_column}.")
    for row in rows.itertuples(index=False):
        identifier = getattr(row, id_column)
        if not identifier or not row.source_url.startswith(("https://", "http://")):
            raise ValueError("Every publication row needs a report ID and a source URL.")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", row.publication_date):
            raise ValueError(f"{identifier}: publication date must use YYYY-MM-DD.")
        day = pd.Timestamp(row.publication_date).date()
        if row.published_at:
            instant = pd.Timestamp(row.published_at)
            if instant.tzinfo is None or instant.tz_convert("Europe/Warsaw").date() != day:
                raise ValueError(f"{identifier}: publication timestamp must include timezone and match the date.")
    return rows


def member_role(name: str) -> str:
    stem = Path(name).stem.casefold().replace("ł", "l")
    ascii_stem = unicodedata.normalize("NFKD", stem).encode("ascii", "ignore").decode()
    plain = re.sub(r"[^a-z0-9]", "", ascii_stem)
    folder = unicodedata.normalize("NFKD", str(Path(name).parent).casefold()).encode("ascii", "ignore").decode()
    folder = re.sub(r"[^a-z0-9]", "", folder)
    if any(value in plain for value in (
        "platnosci", "wybranedane", "wybraneskonsolidowanedane", "audyt", "rewident", "sprzbad",
        "sprawozdaniezbadania", "przegladu", "review", "oswiadczenie", "oswzarzadu", "oswrn",
        "ocenarn", "ocenarady", "infzarzaud", "infzarzates", "atest", "informacjiniefinansow",
        "sprawozdanieniefinansow", "raportniefinansow",
    )) or any(value in folder for value in ("opinianiezale", "bieglegorewidenta", "sprawozdaniezbadania", "firmyaudytorskiej")):
        return ""
    if any(value in plain for value in ("sprawozdaniezarzadu", "sprzarzadu", "managementreport", "szzd")):
        return "management_report"
    if "listprezes" in plain or "ceoletter" in plain:
        return "ceo_letter"
    if plain.startswith("opispknmsr"):
        return "financial_statement"
    if plain.startswith(("opis", "pozostaleinformacje", "komentarz")):
        return "management_commentary"
    return "financial_statement"


def selected_members(names: list[str], source_type: str, sizes=None) -> dict:
    sizes = sizes or {}
    candidates = defaultdict(list)
    for name in names:
        suffix = Path(name).suffix.lower()
        if suffix not in {".pdf", ".xhtml", ".html", ".htm", ".zip", ".xbri"}:
            continue
        role = member_role(name)
        if role:
            candidates[role].append(name)
    if source_type == "management_report" and not candidates["management_report"]:
        if len(candidates["financial_statement"]) == 1:
            candidates["management_report"] = candidates.pop("financial_statement")
    for role in list(candidates):
        if source_type == "management_report" and role != "management_report":
            del candidates[role]
    def best(name):
        stem = Path(name).stem.casefold()
        return (
            bool(re.search(r"(?:_en|_eng|-en|english)(?:$|[._ -])", stem)),
            not any(marker in stem for marker in ("raport", "ssf", "sprfinan", "sprawozdanie", "pkn msr")),
            Path(name).suffix.lower() in {".zip", ".xbri"},
            -sizes.get(name, 0),
            name,
        )
    return {role: min(files, key=best) for role, files in candidates.items() if files}


def archive_payloads(source: Path, source_type: str, signature: bytes) -> list[tuple[str, str, bytes]]:
    if signature.startswith(b"PK\x03\x04"):
        with ZipFile(source) as archive:
            sizes = {entry.filename: entry.file_size for entry in archive.infolist() if not entry.is_dir()}
            entries = [(role, name, archive.read(name))
                       for role, name in selected_members(list(sizes), source_type, sizes).items()]
    else:
        executable = shutil.which("bsdtar") or shutil.which("tar")
        if not executable:
            raise RuntimeError("Reading TAURON 7z packages requires bsdtar (libarchive).")
        listing = subprocess.run([executable, "-tf", str(source)], capture_output=True, check=True)
        names = [
            member.rsplit(b"/", 1)[-1].decode("ascii") for member in listing.stdout.splitlines()
            if member.rsplit(b"/", 1)[-1].isascii()
        ]
        entries = []
        for role, name in selected_members(names, source_type).items():
            if names.count(name) != 1:
                raise ValueError(f"Ambiguous archive basename {source.name}: {name}")
            payload = subprocess.run(
                [executable, "-xOf", str(source), "--", "*" + name], capture_output=True, check=True,
            ).stdout
            entries.append((role, name, payload))
    output = []
    for role, name, payload in entries:
        if not payload.startswith(b"PK\x03\x04"):
            output.append((role, name, payload))
        else:
            # An ESEF package may contain a further ZIP with the XHTML filing.
            with ZipFile(BytesIO(payload)) as inner:
                sizes = {entry.filename: entry.file_size for entry in inner.infolist() if not entry.is_dir()}
                for nested_role, nested in selected_members(list(sizes), "periodic_statement", sizes).items():
                    if Path(nested).suffix.lower() not in {".zip", ".xbri"}:
                        output.append((nested_role, name + "!/" + nested, inner.read(nested)))
    return output


def recognize_image_pdf(source):
    """Use the installed Windows Polish OCR engine without network access."""
    if sys.platform != "win32" or not (powershell := shutil.which("powershell.exe")):
        return ""
    import pymupdf

    with TemporaryDirectory() as temporary:
        if isinstance(source, bytes):
            document = pymupdf.open(stream=source, filetype="pdf")
        else:
            document = pymupdf.open(source)
        with document:
            for index, page in enumerate(document):
                scale = min(2.5, 3000 / max(page.rect.width, page.rect.height))
                png = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), colorspace=pymupdf.csGRAY)
                png.save(Path(temporary) / f"{index:06}.png")
        script = Path(__file__).with_name("ocr_pages.ps1").read_text(encoding="utf-8")
        command = "& {\n" + script + "\n} -PageDirectory $env:MAGISTERKA_OCR_PAGE_DIR"
        encoded = base64.b64encode(command.encode("utf-16-le")).decode("ascii")
        try:
            parsed = subprocess.run(
                [powershell, "-NoProfile", "-NonInteractive", "-EncodedCommand", encoded],
                env={**os.environ, "MAGISTERKA_OCR_PAGE_DIR": temporary},
                capture_output=True, encoding="utf-8", check=True, timeout=240,
                creationflags=subprocess.CREATE_NO_WINDOW,
            )
            return "\n\n".join(json.loads(parsed.stdout)).strip()
        except (subprocess.SubprocessError, OSError, ValueError) as error:
            print(f"Local Polish OCR unavailable for a scanned PDF ({type(error).__name__}).", flush=True)
            return ""


def read_pdf_component(source, role, basis, extract_pdf_text):
    text, _, status = extract_pdf_text(source)
    if status == "low_text" and role in {"presentation", "ceo_letter"}:
        recognized = recognize_image_pdf(source)
        if len(recognized) >= 100:
            return recognized, "ok", basis + "_ocr_pl"
    return text, status, basis


def read_source(source: Path, source_type: str, extract_pdf_text):
    with source.open("rb") as stream:
        signature = stream.read(6)
    if signature.startswith((b"PK\x03\x04", b"7z\xbc\xaf\x27\x1c")):
        entries = archive_payloads(source, source_type, signature)
        for role, member, payload in entries:
            if payload.startswith(b"%PDF-"):
                text, status, basis = read_pdf_component(payload, role, "archive_pdf", extract_pdf_text)
                yield role, member, text, status, basis
            else:
                text = text_from_xhtml(payload)
                yield role, member, text, "ok" if len(text) >= 100 else "low_text", "archive_xhtml"
        return
    role = "financial_statement" if source_type in {"periodic_statement", "consolidated_package"} else source_type
    if source.suffix.lower() in {".xhtml", ".html", ".htm"}:
        text = text_from_xhtml(source.read_bytes())
        yield role, "", text, "ok" if len(text) >= 100 else "low_text", "xhtml"
    else:
        text, status, basis = read_pdf_component(source, role, "pdf", extract_pdf_text)
        yield role, "", text, status, basis


def split_narrative(text: str) -> tuple[str, str]:
    """Extract explicit commentary or connected prose in the explanatory notes."""
    headings = re.compile(
        r"(?im)^[ \t]*(?:\d+(?:\.\d+)*\.? *)?(?:pozostałe informacje do (?:rozszerzonego )?skonsolidowanego "
        r"raportu|sprawozdanie zarządu z działalności)(?:[ \t]+[^.\n]{0,65})?[ \t]*$",
    )
    starts = [match.end() for match in headings.finditer(text) if match.start() >= len(text) // 5]
    if starts:
        section = text[starts[0]:].strip()
        if len(section) >= 400 and INVESTMENT_LANGUAGE.search(section):
            return "management_commentary", section
    # PDF line breaks are visual. Keep complete sentences with explanatory prose.
    source = re.sub(r"\s+", " ", text)
    parts = [
        part.strip() for part in re.split(r"(?<=[.!?])\s+(?=[A-ZĄĆĘŁŃÓŚŹŻ])", source)
        if 90 <= len(part.strip()) <= 3500 and len(WORD_RE.findall(part)) >= 12
    ]
    relevant = {i for i, part in enumerate(parts) if INVESTMENT_LANGUAGE.search(part)}
    if relevant:
        indices = sorted({j for i in relevant for j in range(max(0, i - 1), min(len(parts), i + 2))})
        parts = [parts[i] for i in indices]
    return "financial_notes", "\n\n".join(parts)


def make_manifest(docs: list[dict], extract_pdf_text) -> pd.DataFrame:
    old = read_input(REPORT_MANIFEST, ["document_id", "text_path", "source_path", "archive_member",
                                      "text_basis", "extract_status"])
    old_docs = old.set_index("document_id").to_dict("index")
    protected = set(read_input(METADATA / "investment_passages.csv", PASSAGE_COLUMNS)["document_id"])
    protected |= set(read_input(METADATA / "sentiment_validation_pool.csv", POOL_COLUMNS)["document_id"])
    outputs = CORPUS / "report_texts"
    outputs.mkdir(parents=True, exist_ok=True)
    research_tickers = set(load_study_scope()["tickers"])
    has_separate_narrative = {
        (row["ticker"], row["year"], row["period"]) for row in docs
        if row["doc_type"] in {"management_report", "management_commentary"}
    }
    rows = []
    for doc in docs:
        source = Path(doc["abs_path"])
        stem = source.stem
        components = list(read_source(source, doc["doc_type"], extract_pdf_text))
        components.sort(key=lambda item: {"management_report": 0, "financial_statement": 1,
                                          "management_commentary": 2}.get(item[0], 3))
        known_roles = {item[0] for item in components}
        extracted = []
        for i, (kind, member, body, status, basis) in enumerate(components):
            identifier = stem if i == 0 else f"{stem}__{kind}"
            if identifier in protected:
                original = old_docs.get(identifier)
                if not original or original["source_path"] != data_relative(source):
                    raise ValueError(f"Missing original text for registered offsets: {identifier}")
                text_path = resolve_data_file(original["text_path"])
                body = text_path.read_text(encoding="utf-8")
                member, basis, status = original["archive_member"], original["text_basis"], original["extract_status"]
            else:
                text_path = outputs / f"{identifier}.txt"
                text_path.write_text(body, encoding="utf-8")
            extracted.append((identifier, kind, member, text_path, basis, status))
            if (kind == "financial_statement" and status == "ok"
                    and not known_roles & {"management_report", "management_commentary"}
                    and (doc["ticker"], doc["year"], doc["period"]) not in has_separate_narrative):
                role, narrative = split_narrative(body)
                if len(narrative) >= 100:
                    identifier = f"{stem}__narrative"
                    path = outputs / f"{identifier}.txt"
                    if identifier in protected:
                        if identifier not in old_docs:
                            raise ValueError(f"Missing original text for registered offsets: {identifier}")
                        path = resolve_data_file(old_docs[identifier]["text_path"])
                    else:
                        path.write_text(narrative, encoding="utf-8")
                    extracted.append((identifier, role, member, path, f"narrative_from_{basis}", "ok"))
        for identifier, kind, member, path, basis, status in extracted:
            rows.append({
                "report_id": f"{doc['ticker']}-{doc['year']}-{doc['period']}",
                "document_id": identifier,
                "ticker": doc["ticker"],
                "fiscal_year": doc["year"],
                "period": doc["period"],
                "document_type": kind,
                "is_narrative": kind in NARRATIVE_TYPES,
                "sample_role": "study" if doc["ticker"] in research_tickers else "validation_candidate",
                "source_path": data_relative(source),
                "archive_member": member,
                "text_path": data_relative(path),
                "text_basis": basis,
                "extract_status": status,
            })
    columns = ["report_id", "document_id", "ticker", "fiscal_year", "period", "document_type",
               "is_narrative", "sample_role", "source_path", "archive_member", "text_path", "text_basis", "extract_status"]
    manifest = pd.DataFrame(rows, columns=columns)
    if manifest["document_id"].duplicated().any():
        raise ValueError("Duplicate document identifier in corpus.")
    manifest = manifest.merge(load_publications(METADATA / "report_publications.csv"), on="report_id",
                              how="left", validate="many_to_one")
    has_separate_publication = manifest["document_type"].isin({"presentation", "integrated_report"}) | (
        manifest["document_type"].eq("ceo_letter") & manifest["archive_member"].eq("")
    )
    manifest.loc[has_separate_publication, PUBLICATION_COLUMNS[1:]] = ""
    doc_publications = load_publications(METADATA / "report_document_publications.csv", "document_id")
    if not doc_publications.empty:
        manifest = manifest.merge(doc_publications, on="document_id", how="left", validate="one_to_one",
                                  suffixes=("", "_document"))
        has_override = manifest["source_url_document"].notna()
        for field in PUBLICATION_COLUMNS[1:]:
            manifest[field] = manifest.pop(field + "_document").where(has_override, manifest[field])
    published = pd.to_datetime(manifest["published_at"], utc=True, errors="coerce", format="mixed")
    manifest["publication_time"] = published.dt.tz_convert("Europe/Warsaw").dt.strftime("%H:%M:%S")
    manifest["publication_precision"] = np.select(
        [published.notna(), manifest["publication_date"].fillna("").ne("")], ["timestamp", "date"], default="unknown",
    )
    manifest["is_supplementary"] = manifest["document_type"].isin({"presentation", "ceo_letter", "integrated_report"})
    return manifest.fillna("")


def load_lexicon(path: Path) -> dict:
    def normalize(token: str) -> str:
        return token.casefold().translate(str.maketrans("ąćęłńóśźż", "acelnoszz"))

    lexicon = json.loads(path.read_text(encoding="utf-8"))
    rules = {}
    for rule in lexicon["expressions"]:
        patterns = tuple(normalize(part) for part in rule["expression"].split())
        if patterns in rules or not all(re.fullmatch(r"[a-z]+\*?", token) for token in patterns):
            raise ValueError(f"Invalid or repeated lexicon expression: {rule['expression']}")
        if rule["polarity"] not in (-1, 1):
            raise ValueError("Lexicon polarities must be -1 or 1.")
        rules[patterns] = rule["polarity"]
    lookup = defaultdict(list)
    for parts, polarity in sorted(rules.items(), key=lambda pair: -len(pair[0])):
        lookup[parts[0][0]].append((parts, polarity))
    return {"normalize": normalize, "rules": lookup,
            "negators": {normalize(word) for word in lexicon["negators"]},
            "join_wrapped_lines": lexicon.get("join_wrapped_lines", False),
            "version": lexicon["version"]}


def score_passage(text: str, lexicon: dict) -> dict:
    normalize = lexicon["normalize"]
    negative = positive = word_count = 0
    if lexicon.get("join_wrapped_lines", False):
        # A PDF line wrap can split a phrase. Keep paragraph and sentence boundaries.
        text = re.sub(r"(?<=\S)[ \t\u00a0]*\r?\n[ \t\u00a0]*(?=\S)", " ", text)
    for segment in re.split(r"[.;!?:,\n]+", text):
        words = [normalize(word) for word in WORD_RE.findall(segment)]
        word_count += len(words)
        i = 0
        while i < len(words):
            for pattern, polarity in lexicon["rules"].get(words[i][0], ()):
                candidates = words[i:i + len(pattern)]
                if len(candidates) != len(pattern):
                    continue
                if all(word.startswith(part[:-1]) if part.endswith("*") else word == part
                       for word, part in zip(candidates, pattern)):
                    negators = sum(
                        words[pos] in lexicon["negators"]
                        and words[pos:pos + 2] != ["nie", "tylko"]
                        for pos in range(max(0, i - 2), i)
                    )
                    if negators % 2:
                        polarity *= -1
                    positive += int(polarity > 0)
                    negative += int(polarity < 0)
                    i += len(pattern)
                    break
            else:
                i += 1
    return {"n_words": word_count, "n_positive": positive, "n_negative": negative,
            "tone_per_100_words": 100 * (positive - negative) / word_count if word_count else None}


def extract_registered_spans(frame: pd.DataFrame, manifest: pd.DataFrame) -> list[dict]:
    documents = manifest.set_index("document_id").to_dict("index")
    texts = {}
    records = []
    for row in frame.to_dict("records"):
        identifier = row["document_id"]
        doc = documents.get(identifier)
        if doc is None or doc["extract_status"] != "ok":
            raise ValueError(f"Unavailable document in span registry: {identifier}")
        if identifier not in texts:
            texts[identifier] = resolve_data_file(doc["text_path"]).read_text(encoding="utf-8")
        start, end = int(row["start_char"]), int(row["end_char"])
        if not 0 <= start < end <= len(texts[identifier]):
            raise ValueError(f"Invalid offsets in {identifier}: {start}, {end}")
        fragment = texts[identifier][start:end]
        records.append({
            **row, "start_char": start, "end_char": end, "report_id": doc["report_id"],
            "ticker": doc["ticker"], "fiscal_year": doc["fiscal_year"],
            "publication_date": doc["publication_date"], "published_at": doc["published_at"],
            "publication_source_url": doc["source_url"], "sample_role": doc["sample_role"],
            "span_id": f"{identifier}:{start}:{end}", "text": fragment,
        })
    return records


def write_passage_scores(manifest: pd.DataFrame, lexicon: dict) -> set[str]:
    registry = read_input(METADATA / "investment_passages.csv", PASSAGE_COLUMNS)
    if registry.duplicated(["document_id", "start_char", "end_char", "project_id"]).any():
        raise ValueError("Duplicate project and document span in investment passage registry.")
    records = extract_registered_spans(registry, manifest)
    previous_span = {}
    for row in sorted(records, key=lambda item: (item["document_id"], item["project_id"], item["start_char"])):
        key = row["document_id"], row["project_id"]
        if row["start_char"] < previous_span.get(key, 0):
            raise ValueError(f"Overlapping investment passages: {key}")
        previous_span[key] = row["end_char"]
    for row in records:
        if not row["project_id"] or not row["source_locator"] or row["sample_role"] != "study":
            raise ValueError("Each investment passage needs a project ID, document locator and study issuer.")
        row.update(score_passage(row["text"], lexicon))
        row["lexicon_version"] = lexicon["version"]
    columns = PASSAGE_COLUMNS + ["report_id", "ticker", "fiscal_year", "publication_date", "published_at",
                                "publication_source_url", "sample_role", "span_id", "text",
                                "n_words", "n_positive", "n_negative", "tone_per_100_words", "lexicon_version"]
    pd.DataFrame(records, columns=columns).to_parquet(PASSAGE_SCORES, index=False)
    return {row["report_id"] for row in records}


def tone_class(score: float, cutoff: float) -> str:
    if score < -cutoff:
        return "negative"
    return "positive" if score > cutoff else "neutral"


def validation_metrics(scores: np.ndarray, observed: list[str], cutoff: float) -> list[dict]:
    predicted = np.array([tone_class(score, cutoff) for score in scores])
    actual = np.array(observed)
    metrics = []
    for label in LABELS:
        support = int(np.sum(actual == label))
        calls = int(np.sum(predicted == label))
        hits = int(np.sum((actual == label) & (predicted == label)))
        metrics.append({
            "label": label, "support": support, "predicted": calls,
            "precision": hits / calls if calls else None,
            "recall": hits / support if support else None,
            "f1": 2 * hits / (support + calls) if support + calls else None,
        })
    return metrics


def write_blind_sample(records: list[dict], path: Path) -> None:
    rows = []
    old_labels = {}
    if path.exists():
        previous = read_input(path, ["item_id", "text", "reviewer_label"])
        old_labels = {(r.item_id, r.text): r.reviewer_label for r in previous.itertuples(index=False)}
    for row in records:
        key = hashlib.sha256(row["span_id"].encode("utf-8")).hexdigest()[:16]
        rows.append({"item_id": key, "text": row["text"],
                     "reviewer_label": old_labels.get((key, row["text"]), "")})
    output = pd.DataFrame(rows, columns=["item_id", "text", "reviewer_label"])
    output_keys = set(zip(output.item_id, output.text))
    if any(label and key not in output_keys for key, label in old_labels.items()):
        raise ValueError(f"Sample selection changed in {path.name}; preserve existing labels before regenerating.")
    if path.exists() and previous.equals(output):
        return
    output.to_csv(path, index=False, encoding="utf-8-sig")


def automatic_validation_pool(manifest: pd.DataFrame, investment_reports: set[str]) -> pd.DataFrame:
    references = read_input(REFERENCE_LIST, ["reference_report_id"])
    excluded = investment_reports | set(references["reference_report_id"])
    usable = manifest.loc[
        manifest["is_narrative"] & ~manifest["is_supplementary"] & manifest["extract_status"].eq("ok")
        & manifest["publication_date"].ne("") & ~manifest["report_id"].isin(excluded)
    ].copy()
    priority = {"management_report": 0, "management_commentary": 1, "financial_notes": 2}
    usable["priority"] = usable["document_type"].map(priority)
    reports = usable.sort_values(["priority", "document_id"]).drop_duplicates("report_id")
    records = []
    for _, group in reports.sort_values(["ticker", "fiscal_year", "report_id"]).groupby("ticker"):
        for i, doc in enumerate(group.itertuples(index=False)):
            source = resolve_data_file(doc.text_path).read_text(encoding="utf-8")
            words = list(WORD_RE.finditer(source))
            options = []
            for index in range(0, len(words) - 42, 58):
                start, end = words[index].start(), words[index + 42].end()
                fragment = source[start:end]
                if len(fragment) <= 775 and INVESTMENT_LANGUAGE.search(fragment):
                    options.append((start, end))
            split = "calibration" if i % 4 == 0 else "holdout"
            seed = int(hashlib.sha256(doc.report_id.encode("utf-8")).hexdigest()[:8], 16)
            random = np.random.default_rng(seed)
            for choice in sorted(random.permutation(len(options))[:4]):
                start, end = options[choice]
                records.append({"document_id": doc.document_id, "start_char": start, "end_char": end, "split": split})
    return pd.DataFrame(records, columns=POOL_COLUMNS)


def passage_tones(records, lexicon):
    scores = np.array([score_passage(row["text"], lexicon)["tone_per_100_words"] for row in records], dtype=float)
    if not np.isfinite(scores).all():
        raise ValueError("No words detected in a validation fragment.")
    return scores


def calibration_cutoff(scores, labels):
    candidates = np.unique(np.append(0.0, np.abs(scores)))
    return float(max(candidates, key=lambda cutoff: np.mean([
        item["f1"] or 0.0 for item in validation_metrics(scores, labels, cutoff)
    ])))


def blind_labels(selection, filename):
    if not selection:
        return []
    path = VALIDATION / filename
    write_blind_sample(selection, path)
    labels = read_input(path, ["reviewer_label"])["reviewer_label"].tolist()
    if any(label and label not in LABELS for label in labels):
        raise ValueError(f"Unknown label in {path.name}.")
    return labels


def run_validation(manifest: pd.DataFrame, investment_reports: set[str], lexicon: dict) -> dict:
    pool = read_input(METADATA / "sentiment_validation_pool.csv", POOL_COLUMNS)
    origin = "reviewer_registry"
    if pool.empty:
        pool = automatic_validation_pool(manifest, investment_reports)
        origin = "automatic_topic_screen"
    records = extract_registered_spans(pool, manifest)
    if any(row["split"] not in {"calibration", "holdout"} for row in records):
        raise ValueError("Validation split must be calibration or holdout.")
    if len({row["span_id"] for row in records}) != len(records):
        raise ValueError("Validation pool includes duplicate spans.")
    by_split = {split: [row for row in records if row["split"] == split] for split in ("calibration", "holdout")}
    cal_reports = {row["report_id"] for row in by_split["calibration"]}
    holdout_reports = {row["report_id"] for row in by_split["holdout"]}
    if holdout_reports & (cal_reports | investment_reports):
        raise ValueError("Holdout reports must differ from calibration and event-study reports.")
    VALIDATION.mkdir(parents=True, exist_ok=True)
    if origin == "automatic_topic_screen":
        pool.to_csv(VALIDATION / "validation_pool_auto.csv", index=False, encoding="utf-8-sig")
    available = by_split["holdout"]
    sampled = []
    if len(available) >= 100:
        groups = defaultdict(list)
        for row in sorted(available, key=lambda item: item["span_id"]):
            groups[row["ticker"], row["fiscal_year"]].append(row)
        if len({key[0] for key in groups}) < 2 or len({key[1] for key in groups}) < 2:
            raise ValueError("Holdout must span multiple issuers and years.")
        random = np.random.default_rng(42)
        for group in groups.values():
            random.shuffle(group)
        while len(sampled) < 100:
            for position in random.permutation(len(groups)):
                group = list(groups.values())[position]
                if group and len(sampled) < 100:
                    sampled.append(group.pop())
    result = {"status": "pending_review", "calibration_pool": len(by_split["calibration"]),
              "holdout_pool": len(available), "holdout_size": len(sampled),
              "pool_origin": origin,
              "holdout_by_ticker": dict(Counter(row["ticker"] for row in sampled)),
              "lexicon_version": lexicon["version"], "neutral_cutoff": None, "holdout_metrics": []}
    calibration = by_split["calibration"]
    calibration_labels = blind_labels(calibration, "calibration_blind.csv")
    versions = {lexicon["version"]: lexicon}
    baseline = METADATA / "investment_tone_lexicon_v0.1.json"
    if baseline.is_file() and lexicon["version"] != "investment-pl-0.1":
        archived = load_lexicon(baseline)
        versions[archived["version"]] = archived
    cutoffs = {}
    if calibration and set(calibration_labels) == set(LABELS):
        cutoffs = {version: calibration_cutoff(passage_tones(calibration, model), calibration_labels)
                   for version, model in versions.items()}
        result["neutral_cutoff"] = cutoffs[lexicon["version"]]

    holdout_labels = blind_labels(sampled, "validation_blind.csv")
    result["reviewed_calibration"] = sum(bool(value) for value in calibration_labels)
    result["reviewed_holdout"] = sum(bool(value) for value in holdout_labels)
    if cutoffs and sampled and all(holdout_labels):
        comparison = {}
        for version, model in versions.items():
            cutoff = cutoffs[version]
            scored = passage_tones(sampled, model)
            metrics = validation_metrics(scored, holdout_labels, cutoff)
            comparison[version] = {
                "neutral_cutoff": cutoff, "holdout_metrics": metrics,
                "macro_f1": float(np.mean([item["f1"] or 0.0 for item in metrics])),
                "accuracy": float(np.mean([tone_class(score, cutoff) == label
                                           for score, label in zip(scored, holdout_labels)])),
            }
        result["status"] = "evaluated"
        result["holdout_comparison"] = comparison
        result["holdout_metrics"] = comparison[lexicon["version"]]["holdout_metrics"]
    (VALIDATION / "validation_status.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def verify_corpus_coverage(manifest: pd.DataFrame, scope: dict) -> dict:
    references = read_input(REFERENCE_LIST, ["reference_report_id"])
    receipts = REPORTS / "manifest_stage3_bundles.json"
    baseline = set()
    if receipts.exists():
        baseline = {row["report_id"] for row in json.loads(receipts.read_text(encoding="utf-8"))["files"].values()}
    first, last = (int(scope["period"][boundary][:4]) for boundary in ("start", "end"))
    expected = {f"{ticker}-{year}-{period}" for ticker in scope["tickers"]
                for year in range(first, last + 1) for period in CORE_PERIODS}
    reference_ids = set(references["reference_report_id"]) - {""}
    coverage = set(manifest.loc[
        manifest["is_narrative"] & ~manifest["is_supplementary"] & manifest["extract_status"].eq("ok")
        & manifest["publication_date"].ne(""), "report_id",
    ])
    missing = (expected | baseline | reference_ids) - coverage
    if missing:
        raise ValueError("Reports without dated narrative text: " + ", ".join(sorted(missing)))
    return {"core_reports": len(expected & coverage), "baseline_reports": len(baseline & coverage),
            "reference_reports": len(reference_ids & coverage), "reference_events": len(references)}


def build_current_corpus(docs: list[dict], extract_pdf_text) -> None:
    CORPUS.mkdir(parents=True, exist_ok=True)
    SENTIMENT.mkdir(parents=True, exist_ok=True)
    manifest = make_manifest(docs, extract_pdf_text)
    coverage = verify_corpus_coverage(manifest, load_study_scope())
    manifest.to_csv(REPORT_MANIFEST, index=False, encoding="utf-8-sig")
    lexicon = load_lexicon(METADATA / "investment_tone_lexicon.json")
    reviewed = write_passage_scores(manifest, lexicon)
    validation = run_validation(manifest, reviewed, lexicon)
    study = manifest[manifest["sample_role"].eq("study")]
    print(f"Documents: {len(study)} study ({study['extract_status'].eq('ok').sum()} extracted), "
          f"{len(manifest) - len(study)} external; "
          f"reports with verified publication dates: {study.loc[study['publication_date'].ne(''), 'report_id'].nunique()}; "
          f"reviewed investment reports: {len(reviewed)}; validation: {validation['status']}; "
          f"coverage: {coverage}; blind holdout: {validation['holdout_size']}")
