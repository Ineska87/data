"""Prepare the reviewed document, passage, and validation datasets for the study."""

from __future__ import annotations

from collections import defaultdict
import hashlib
import json
from pathlib import Path
import re
import subprocess
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
AR_PACKAGE = re.compile(r"TPE_20(?:20|21|22|23|24|25)_AR_skonsolidowany\.(?:pdf|zip|7z)$", re.I)
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
    page = html.fromstring(xhtml, parser=html.HTMLParser(encoding="utf-8", no_network=True))
    for el in page.xpath("//script|//style|//head|//*[name()='ix:header' or name()='ix:hidden']"):
        el.drop_tree()
    blocks = [" ".join(line.split()) for line in page.text_content().splitlines() if line.strip()]
    text = "\n".join(blocks)
    if len(text) < 100:
        raise ValueError(f"{path.name}: management XHTML has no usable text")
    return text, member


def read_orlen_archive(path: Path, extract_pdf_text) -> tuple[str, str, str]:
    """Select the principal report from the three verified ORLEN pilot packages."""
    with ZipFile(path) as archive:
        reports = [entry for entry in archive.infolist() if entry.filename.lower().endswith(".pdf")]
        if not reports:
            raise ValueError(f"{path.name}: archive contains no PDF")
        member = max(reports, key=lambda entry: entry.file_size)
        text, _, status = extract_pdf_text(archive.read(member))
    return text, member.filename, status


def load_publications(path: Path) -> pd.DataFrame:
    rows = read_input(path, PUBLICATION_COLUMNS)[PUBLICATION_COLUMNS]
    if rows["report_id"].duplicated().any():
        raise ValueError("The publication registry has duplicate report IDs.")
    for row in rows.itertuples(index=False):
        if not row.report_id or not row.source_url.startswith(("https://", "http://")):
            raise ValueError("Every publication row needs a report ID and a source URL.")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", row.publication_date):
            raise ValueError(f"{row.report_id}: publication date must use YYYY-MM-DD.")
        day = pd.Timestamp(row.publication_date).date()
        if row.published_at:
            instant = pd.Timestamp(row.published_at)
            if instant.tzinfo is None or instant.tz_convert("Europe/Warsaw").date() != day:
                raise ValueError(f"{row.report_id}: publication timestamp must include timezone and match the date.")
    return rows


def make_manifest(docs: list[dict], extract_pdf_text) -> pd.DataFrame:
    previous_path = CORPUS / "manifest.csv"
    prior = read_input(previous_path, ["filename", "text_path", "extract_status"])
    prior = {Path(row.filename).stem: row for row in prior.itertuples(index=False)}
    outputs = CORPUS / "report_texts"
    outputs.mkdir(parents=True, exist_ok=True)
    research_tickers = set(load_study_scope()["tickers"])
    rows = []
    for doc in docs:
        source = Path(doc["abs_path"])
        stem = source.stem
        ar_member = ""
        cached = prior.get(stem)
        if AR_PACKAGE.fullmatch(source.name):
            text, ar_member = read_management_archive(source)
            text_path = outputs / f"{stem}.txt"
            text_path.write_text(text, encoding="utf-8")
            status = "ok"
            text_basis = "management_xhtml"
        elif source.name in ORLEN_PILOT_PACKAGES:
            text, ar_member, status = read_orlen_archive(source, extract_pdf_text)
            text_path = outputs / f"{stem}.txt"
            text_path.write_text(text, encoding="utf-8")
            text_basis = "periodic_report_pdf_from_zip"
        elif cached and cached.extract_status == "ok" and resolve_data_file(cached.text_path).is_file():
            text_path = resolve_data_file(cached.text_path)
            status = cached.extract_status
            text_basis = cached.segment
        else:
            text, _, status = extract_pdf_text(source)
            text_path = outputs / f"{stem}.txt"
            text_path.write_text(text, encoding="utf-8")
            text_basis = "pdf"
        rows.append({
            "report_id": f"{doc['ticker']}-{doc['year']}-{doc['period']}",
            "document_id": stem,
            "ticker": doc["ticker"],
            "fiscal_year": doc["year"],
            "period": doc["period"],
            "document_type": doc["doc_type"],
            "sample_role": "study" if doc["ticker"] in research_tickers else "validation_candidate",
            "source_path": data_relative(source),
            "archive_member": ar_member,
            "text_path": data_relative(text_path),
            "text_basis": text_basis,
            "extract_status": status,
        })
    columns = ["report_id", "document_id", "ticker", "fiscal_year", "period", "document_type",
               "sample_role", "source_path", "archive_member", "text_path", "text_basis", "extract_status"]
    manifest = pd.DataFrame(rows, columns=columns)
    if manifest["document_id"].duplicated().any():
        raise ValueError("Duplicate document identifier in corpus.")
    return manifest.merge(load_publications(METADATA / "report_publications.csv"), on="report_id",
                          how="left", validate="many_to_one").fillna("")


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
            "version": lexicon["version"]}


def score_passage(text: str, lexicon: dict) -> dict:
    normalize = lexicon["normalize"]
    negative = positive = word_count = 0
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
    output.to_csv(path, index=False, encoding="utf-8-sig")


def run_validation(manifest: pd.DataFrame, investment_reports: set[str], lexicon: dict) -> dict:
    pool = read_input(METADATA / "sentiment_validation_pool.csv", POOL_COLUMNS)
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
              "lexicon_version": lexicon["version"], "neutral_cutoff": None, "holdout_metrics": []}
    labels = {}
    for split, selection in (("calibration", by_split["calibration"]), ("validation", sampled)):
        if selection:
            file = VALIDATION / f"{split}_blind.csv"
            write_blind_sample(selection, file)
            labels[split] = read_input(file, ["reviewer_label"])["reviewer_label"].tolist()
            if any(label and label not in LABELS for label in labels[split]):
                raise ValueError(f"Unknown label in {file.name}.")
    calibration = by_split["calibration"]
    if calibration and set(labels["calibration"]) == set(LABELS):
        scores = np.array([score_passage(row["text"], lexicon)["tone_per_100_words"] for row in calibration], dtype=float)
        if not np.isfinite(scores).all():
            raise ValueError("No words detected in a calibration fragment.")
        candidates = np.unique(np.append(0.0, np.abs(scores)))
        cutoff = max(candidates, key=lambda value: np.mean([
            item["f1"] or 0.0 for item in validation_metrics(scores, labels["calibration"], value)
        ]))
        result["neutral_cutoff"] = float(cutoff)
        if sampled and all(labels["validation"]):
            scored = np.array([score_passage(row["text"], lexicon)["tone_per_100_words"] for row in sampled], dtype=float)
            if not np.isfinite(scored).all():
                raise ValueError("No words detected in a validation fragment.")
            result["status"] = "evaluated"
            result["holdout_metrics"] = validation_metrics(scored, labels["validation"], cutoff)
    (VALIDATION / "validation_status.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    return result


def build_current_corpus(docs: list[dict], extract_pdf_text) -> None:
    CORPUS.mkdir(parents=True, exist_ok=True)
    SENTIMENT.mkdir(parents=True, exist_ok=True)
    manifest = make_manifest(docs, extract_pdf_text)
    manifest.to_csv(REPORT_MANIFEST, index=False, encoding="utf-8-sig")
    lexicon = load_lexicon(METADATA / "investment_tone_lexicon.json")
    reviewed = write_passage_scores(manifest, lexicon)
    validation = run_validation(manifest, reviewed, lexicon)
    study = manifest[manifest["sample_role"].eq("study")]
    print(f"Documents: {len(study)} study ({study['extract_status'].eq('ok').sum()} extracted), "
          f"{len(manifest) - len(study)} external; "
          f"reports with verified publication dates: {study.loc[study['publication_date'].ne(''), 'report_id'].nunique()}; "
          f"reviewed investment reports: {len(reviewed)}; validation: {validation['status']}")
