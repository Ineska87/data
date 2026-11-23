"""Prepare a local evidence worksheet for manual review of the ESPI candidates."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import csv
from functools import lru_cache
import io
import json
from pathlib import Path
import re

import pymupdf

from data_paths import DATA_ROOT, EVENTS, METADATA, PROCESSED, RAW
from espi_investment_evidence import write_text
from publication_order import publication_clock, strictly_before


EVIDENCE = RAW / "espi" / "detail_evidence"
CELL_LIMIT = 30_000
REVIEW_FIELDS = (
    "manual_review_status", "manual_project_id", "manual_decision_type",
    "manual_adverse_revision", "manual_scope_comparable", "manual_milestone_comparable",
    "manual_first_public_plan_event_id", "manual_first_public_plan_url",
    "manual_first_public_plan_date", "manual_first_public_plan_time", "manual_first_public_plan_time_source_url",
    "manual_previous_plan_event_id", "manual_previous_plan_url",
    "manual_previous_plan_date", "manual_previous_plan_time", "manual_previous_plan_time_source_url",
    "manual_previous_capex", "manual_new_capex", "manual_capex_currency",
    "manual_previous_scope", "manual_new_scope",
    "manual_previous_milestone_type", "manual_new_milestone_type",
    "manual_previous_milestone_date", "manual_new_milestone_date",
    "manual_actual_spend", "manual_actual_spend_currency", "manual_actual_spend_to",
    "manual_impairment", "manual_impairment_currency", "manual_impairment_period",
    "manual_comparison_source_url", "manual_coding_note",
)
NUMBER = r"(?:\d{1,3}(?:[ \u00a0\u202f]\d{3})+(?:[,.]\d+)?|\d+(?:[,.]\d+)?)"
SCALE = r"(?:tys\.?|mln\.?|mld\.?|milion\w*|miliard\w*)"
CURRENCY = r"(?:PLN|zł(?:otych|ote|oty)?|EUR|euro|USD|GBP)"
MONEY = re.compile(
    rf"(?<!\w)(?P<raw>(?:{NUMBER}(?:\s*[–—-]\s*{NUMBER})?\s*(?:{SCALE}\s*)?{CURRENCY}"
    rf"|(?:PLN|EUR|USD|GBP)\s*{NUMBER}(?:\s*[–—-]\s*{NUMBER})?(?:\s*{SCALE})?))(?!\w)",
    re.IGNORECASE,
)
DATE = re.compile(
    r"\b(?:20\d{2}-\d{2}-\d{2}|\d{1,2}[./]\d{1,2}[./]20\d{2}"
    r"|\d{1,2}\s+(?:stycznia|lutego|marca|kwietnia|maja|czerwca|lipca|sierpnia|września"
    r"|października|listopada|grudnia)\s+20\d{2}"
    r"|(?:I{1,3}|IV|[1-4])\.?\s+(?:kwartał\w*|kw\.|półrocz\w*)\s+20\d{2}"
    r"|(?:końc\w*|początk\w*|do)\s+(?:roku\s+)?20\d{2})\b",
    re.IGNORECASE,
)
PROJECTS = {
    "Olefiny III / Nowa Chemia": r"\bolefin(?:y|ach|om)?\s*(?:III|3)\b|\bnow(?:a|ej|ą)\s+chemi|\bkompleks\w*\s+olefin",
    "Ostrołęka": r"\bostrołęk\w*|\bccgt\s+ostrołęk",
    "Dolna Odra / Gryfino 2050": r"\bdoln\w*\s+odr\w*|\bgryfino\s+2050\b|\bpge\s+gryfino\b",
    "Turów": r"\btur(?:ów|ow\w*)\b",
    "Baltica 2": r"\bbaltica\s*[-–]?\s*2\b",
    "Baltica": r"\b(?:mfw\s+)?baltica\b",
    "Baltic Power": r"\bbaltic\s+power\b",
    "Nowa EC Czechnica": r"\bczechnic\w*|\bsiechnic\w*",
    "Rybnik": r"\brybni(?:k|k[au]|ck\w*)\b",
    "Magazyn energii w Żarnowcu": r"\bżarnow(?:iec|c\w*)\b",
    "Visbreaking": r"\bvisbreaking\w*",
    "Instalacja HVO": r"\b(?:instalacj\w*|jednostk\w*|produkcj\w*)\s+hvo\b|\buwodornion\w*\s+olej",
    "Bottom of Barrel": r"\bbottom\s+of\s+(?:the\s+)?barrel\b|\bgłębok\w*\s+przerob\w*\s+pozostało",
    "Rozbudowa produkcji nawozów ANWIL": r"\b(?:zdolnoś\w*|moc\w*)\s+produkcyjn\w*\s+nawoz\w*"
    r"|\b(?:budow\w*|instalacj\w*)\s+\w+\s+linie?\s+nawoz",
    "Bioetanol II generacji": r"\bbioetanol\w*",
    "Wytwórnia Tlenu i Azotu III": r"\bwytwórni\w*\s+tlenu\s+i\s+azotu",
    "Jaworzno": r"\bjaworzn\w*",
    "Elektrownia Łagisza": r"\błagisz\w*",
    "Naturalna Energia": r"\bnaturaln\w*\s+energi\w*\b",
    "LOTOS Terminale": r"\blotos\s+terminal\w*",
    "Elektrownia Konin": r"\belektrowni\w*\s+konin\w*|\belektrowni\w*\s+w\s+koninie",
    "Brudzew": r"\bbrudzew\w*",
    "Elektrownia Adamów": r"\badam(?:ów|ow\w*)\b",
    "Enea Elkogaz": r"\belkogaz\w*",
    "Nowotna Farma Wiatrowa": r"\bnowotn\w*\s+farm\w*\s+wiatrow",
}
PROJECT_MATCH = {name: re.compile(expr, re.IGNORECASE) for name, expr in PROJECTS.items()}
CAPEX = re.compile(
    r"\b(?:capex|nakład\w*\s+(?:inwestycyjn\w*|kapitałow\w*)|wydatk\w*\s+inwestycyjn\w*"
    r"|budżet\w*\s+(?:projekt\w*|inwesty\w*)|harmonogram\w*\s+(?:projekt\w*|inwesty\w*|realizac\w*)"
    r"|koszt\w*\s+(?:inwestycj\w*|budow\w*)|odpis\w*\s+aktualiz\w*)\b",
    re.IGNORECASE,
)
AMOUNT_CONTEXT = {
    "impairment": re.compile(r"\bodpis\w*|\butrat\w*\s+wartości", re.IGNORECASE),
    "historical_spend": re.compile(r"\b(?:poniesion\w*|wydatkowano|nakład\w*\s+narastająco)\b", re.IGNORECASE),
    "projected_capex": re.compile(r"\bcapex\b|\bbudżet\w*|\bnakład\w*\s+inwestycyjn\w*"
                                  r"|\bszacowan\w*\s+koszt\w*", re.IGNORECASE),
}
DATE_CONTEXT = {
    "construction_completion": re.compile(r"\bzakończeni\w*\s+(?:budow\w*|prac\w*)", re.IGNORECASE),
    "commissioning": re.compile(r"\brozruch\w*|\bkomercjaliz\w*|\boddani\w*\s+do\s+eksploatac\w*"
                                r"|\buruchomieni\w*", re.IGNORECASE),
}


def read_csv(path):
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def read_jsonl(path):
    with path.open(encoding="utf-8-sig") as stream:
        return [(number, json.loads(line)) for number, line in enumerate(stream, 1) if line.strip()]


def index_unique(items, key, source):
    result = {}
    for row in items:
        if row[key] in result:
            raise ValueError(f"{source}: powtórzony {key} {row[key]}")
        result[row[key]] = row
    return result


def preview(text):
    return " ".join(text.split())


def evidence_window(text, start, end, radius):
    lower, upper = max(0, start - radius), min(len(text), end + radius)
    left = re.search(r"\s", text[lower:start]) if lower else None
    if left:
        lower += left.end()
    right = re.search(r"\s(?=\S*$)", text[end:upper]) if upper < len(text) else None
    if right:
        upper = end + right.start()
    return lower, upper, preview(text[lower:upper])


def numeric_clues(text, source, pattern, tags, maximum=12):
    matches = []
    seen = set()
    for match in pattern.finditer(text):
        lower, upper, quote = evidence_window(text, *match.span(), 110)
        context = text[max(0, match.start() - 75):match.end() + 40]
        kinds = [kind for kind, test in tags.items() if test.search(context)]
        key = preview(match[0]).casefold(), tuple(kinds)
        if key in seen:
            continue
        seen.add(key)
        clue = {
            "mention": preview(match[0]), "kind_hints": kinds, "source": source,
            "start_char": lower, "end_char": upper, "quote": quote,
        }
        if pattern is MONEY:
            currency = re.search(CURRENCY, match[0], re.IGNORECASE)[0].casefold()
            clue["currency"] = "PLN" if currency.startswith("zł") else "EUR" if currency == "euro" else currency.upper()
        matches.append(clue)
    return sorted(matches, key=lambda clue: not bool(clue["kind_hints"]))[:maximum]


def is_earlier(document, reference):
    published = document["publication_date"]
    return bool(published) and strictly_before(
        published, publication_clock(document["published_at"]), reference["event_date"], reference["event_time"],
    ) is True


def local_path(ref):
    path = (DATA_ROOT / ref).resolve()
    if not path.is_relative_to(DATA_ROOT.resolve()):
        raise ValueError(f"Ścieżka poza katalogiem danych: {ref}")
    return path


@lru_cache(maxsize=256)
def read_document(ref):
    return local_path(ref).read_text(encoding="utf-8")


@lru_cache(maxsize=16)
def read_pdf(ref):
    pages = []
    with pymupdf.open(local_path(ref)) as document:
        for index, page in enumerate(document, 1):
            pages.append((index, page.get_text()))
    return pages


def named_projects(candidate, report):
    title = candidate["title"]
    clues = " ".join(candidate.get("full_text_evidence", {}).values())
    matches = [name for name, test in PROJECT_MATCH.items() if test.search(title)]
    if not matches:
        matches = [name for name, test in PROJECT_MATCH.items() if test.search(clues)]
    if candidate.get("mandatory_olefiny") and PROJECT_MATCH["Olefiny III / Nowa Chemia"].search(report["text"]):
        matches.insert(0, "Olefiny III / Nowa Chemia")
    if "Baltica 2" in matches and "Baltica" in matches:
        matches.remove("Baltica")
    return list(dict.fromkeys(matches))


def document_priority(doc):
    kind = doc["document_type"]
    return 0 if ("zarzadu" in kind or "management" in kind or "narrative" in kind) else 1


def periodic_evidence(documents, projects):
    found = []
    for doc in sorted(documents, key=lambda row: (document_priority(row), row["document_id"])):
        text = read_document(doc["text_path"])
        patterns = [("named_project", name, PROJECT_MATCH[name]) for name in projects]
        patterns.append(("general_capex_context", "", CAPEX))
        for match_type, label, pattern in patterns:
            for index, match in enumerate(pattern.finditer(text)):
                if index == 40:
                    break
                start, end, quote = evidence_window(text, *match.span(), 270)
                if len(quote) < 100:
                    continue
                score = (match_type == "named_project", bool(CAPEX.search(quote)), -document_priority(doc))
                found.append((score, {
                    "match_type": match_type, "project_anchor": label, "document_id": doc["document_id"],
                    "document_type": doc["document_type"], "text_path": doc["text_path"],
                    "start_char": start, "end_char": end, "start_line": text.count("\n", 0, start) + 1,
                    "publication_date": doc["publication_date"], "published_at": doc["published_at"], "quote": quote,
                }))
    chosen = []
    for _, passage in sorted(found, key=lambda pair: pair[0], reverse=True):
        if any(
            previous["document_id"] == passage["document_id"]
            and passage["start_char"] < previous["end_char"] and previous["start_char"] < passage["end_char"]
            for previous in chosen
        ):
            continue
        chosen.append(passage)
        if len(chosen) == 3:
            break
    return chosen


def preliminary_code(candidate):
    tags = set(candidate.get("title_evidence", ())) | set(candidate.get("full_text_evidence", ()))
    primary = tags.intersection({"start", "revision", "suspension"})
    if len(primary) == 1:
        decision = next(iter(primary))
    elif not primary and "impairment_under_construction" in tags:
        decision = "check_impairment_or_revision"
    elif not primary and "execution_contract" in tags:
        decision = "check_execution_contract"
    else:
        decision = "manual_disambiguation"
    adverse = "unknown" if decision in {"revision", "suspension", "check_impairment_or_revision"} else ""
    return decision, adverse


def flatten(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")) if value else ""


def spreadsheet_safe(value):
    """Protect text cells when a user opens the CSV in Excel or LibreOffice."""
    probe = value.lstrip("\ufeff \t\r\n\f\v")
    return "'" + value if probe.startswith(("=", "+", "-", "@")) else value


def existing_annotations(path):
    if not path.is_file():
        return {}
    rows = index_unique(read_csv(path), "event_id", path.name)
    return {event_id: {key: row.get(key, "") for key in REVIEW_FIELDS} for event_id, row in rows.items()}


def build(manifest, output, *, allow_incomplete):
    candidates = [row for _, row in read_jsonl(EVIDENCE / "investment_candidates.jsonl")]
    candidate_index = index_unique(candidates, "event_id", "investment_candidates.jsonl")
    reports = index_unique(
        [{**row, "locator": f"raw/espi/detail_evidence/reports.jsonl#L{line}"}
         for line, row in read_jsonl(EVIDENCE / "reports.jsonl")],
        "event_id", "reports.jsonl",
    )
    references = index_unique(
        read_csv(RAW / "reports" / "publication_archive" / "event_periodic_references.csv"),
        "event_id", "event_periodic_references.csv",
    )
    chronology_path = PROCESSED / "corpus" / "candidate_report_chronology.csv"
    chronology = index_unique(read_csv(chronology_path), "event_id", chronology_path.name) if chronology_path.is_file() else {}
    event_rows = index_unique(read_csv(EVENTS / "espi_review_queue.csv"), "event_id", "espi_review_queue.csv")
    reviews = index_unique(read_csv(METADATA / "espi_review.csv"), "event_id", "espi_review.csv")
    attachments, priors, corpus = defaultdict(dict), defaultdict(list), defaultdict(list)
    by_issuer_day = defaultdict(list)
    for row in event_rows.values():
        by_issuer_day[row["ticker"], row["event_date"]].append(row)
    for _, row in read_jsonl(EVIDENCE / "attachments.jsonl"):
        for event_id in row["event_ids"]:
            attachment = {key: row.get(key, "") for key in ("url", "titles", "status", "file")}
            if attachment["file"] and not local_path(attachment["file"]).is_file():
                attachment["status"] = "missing_local_file"
            attachments[event_id][row["url"]] = attachment
    for _, row in read_jsonl(EVIDENCE / "prior_report_links.jsonl"):
        report = reports[row["event_id"]]
        for event_id in row["referenced_by"]:
            priors[event_id].append({
                **{key: row[key] for key in ("event_id", "report_number", "event_date", "url", "title")},
                "locator": report["locator"], "published_time": report.get("publication_time_exact") or report.get("publication_time"),
                "link_evidence": [item for item in row["evidence"] if item["event_id"] == event_id],
            })
    for row in read_csv(manifest):
        if row["extract_status"] == "ok" and row["text_path"] and local_path(row["text_path"]).is_file():
            corpus[row["report_id"]].append(row)

    target = output / "candidates_review_workbench.csv"
    annotations = existing_annotations(target)
    lost = [event for event, fields in annotations.items() if event not in candidate_index and any(fields.values())]
    if lost:
        raise ValueError(f"Zachowano dotychczasowy arkusz z wpisami dla wycofanych kandydatów {lost}.")

    rows = []
    source_parts = max(1, (max(len(reports[event_id]["text"]) for event_id in candidate_index) - 1) // CELL_LIMIT + 1)
    for candidate in sorted(candidates, key=lambda row: (row["ticker"], row["event_date"], row["event_id"])):
        event = candidate["event_id"]
        report, reference = reports[event], references[event]
        official = event_rows[event]
        reference = {**reference, "event_date": official["event_date"], "event_time": official["publication_time"]}
        if report["status"] != "ok" or not report["text"].strip():
            raise ValueError(f"{event}: brak zweryfikowanej pełnej treści ESPI.")
        review = reviews.get(event, {})
        project_names = named_projects(candidate, report)
        espi_assets = dict(attachments[event])
        for item in report.get("attachments") or ():
            if isinstance(item, dict) and item.get("url"):
                espi_assets.setdefault(item["url"], {"url": item["url"], "titles": [item.get("title", "")],
                                                    "status": "source_link", "file": ""})
        earlier = sorted(priors[event], key=lambda item: (item["event_date"], item["event_id"]))
        sources = [(report["locator"], report["text"])]
        sources += [(prior["locator"], reports[prior["event_id"]]["text"]) for prior in earlier]
        for item in espi_assets.values():
            if item["file"] and item["status"] != "missing_local_file":
                sources += [(f"{item['file']}#page={page}", text) for page, text in read_pdf(item["file"])]
        amounts = [value for source, text in sources for value in numeric_clues(text, source, MONEY, AMOUNT_CONTEXT)]
        dates = [value for source, text in sources for value in numeric_clues(text, source, DATE, DATE_CONTEXT, 8)]
        eligible = [doc for doc in corpus.get(reference["reference_report_id"], [])
                    if doc.get("is_narrative", "true").lower() == "true"
                    and doc.get("is_supplementary", "").lower() != "true" and is_earlier(doc, reference)]
        excerpts = periodic_evidence(eligible, project_names)
        excerpt_level = "named_project" if any(p["match_type"] == "named_project" for p in excerpts) else (
            "general_capex_context" if excerpts else "no_match" if eligible else "no_eligible_text"
        )
        code, adverse = preliminary_code(candidate)
        same_day = [
            {key: item[key] for key in ("event_id", "report_number", "publication_time", "title", "url")}
            for item in sorted(by_issuer_day[candidate["ticker"], official["event_date"]],
                               key=lambda row: (row["publication_time"], row["event_id"]))
            if item["event_id"] != event
        ]
        rows.append({
            "event_id": event, "ticker": candidate["ticker"], "event_date": candidate["event_date"],
            "event_time": official["publication_time"], "report_number": candidate["report_number"],
            "title": candidate["title"], "source_url": candidate["url"], "espi_locator": report["locator"],
            "review_status_in_registry": review.get("review_status", "needs_review"),
            "project_id_in_registry": review.get("project_id", ""),
            "decision_type_in_registry": review.get("decision_type", ""),
            "same_issuer_day_candidate_ids": " | ".join(item["event_id"] for item in same_day if item["event_id"] in candidate_index),
            "same_issuer_day_espi": flatten(same_day),
            "manual_review_required": "true", "suggested_decision_type": code,
            "suggested_adverse_revision": adverse, "project_anchors": " | ".join(project_names),
            "candidate_evidence": flatten({
                "by_title": candidate.get("title_evidence", {}), "by_full_text": candidate.get("full_text_evidence", {}),
            }),
            "attachments": flatten(list(espi_assets.values())), "prior_espi_references": flatten(earlier),
            "money_mentions": flatten(amounts), "date_mentions": flatten(dates),
            "reference_report_id": reference["reference_report_id"],
            "reference_publication_date": reference["report_publication_date"],
            "reference_published_at": reference["report_published_at"],
            "reference_source_url": reference["report_source_url"], "reference_status": reference["status"],
            "reference_local_files": reference["local_files"],
            "reference_precedes_espi": chronology.get(event, {}).get("report_precedes_espi", ""),
            "no_newer_periodic_report": chronology.get(event, {}).get("no_newer_periodic_report", ""),
            "newer_periodic_report_ids": chronology.get(event, {}).get("newer_periodic_report_ids", ""),
            "uncertain_periodic_report_ids": chronology.get(event, {}).get("uncertain_periodic_report_ids", ""),
            "eligible_corpus_documents": " | ".join(doc["document_id"] for doc in eligible),
            "periodic_evidence_kind": excerpt_level, "periodic_excerpts": flatten(excerpts),
            **{("espi_text" if part == 0 else f"espi_text_continued_{part + 1}"):
               report["text"][part * CELL_LIMIT:(part + 1) * CELL_LIMIT] for part in range(source_parts)},
            **{key: annotations.get(event, {}).get(key, "") for key in REVIEW_FIELDS},
        })

    stats = summarize(rows)
    if stats["with_eligible_periodic_text"] != len(rows) and not allow_incomplete:
        missing = [row["event_id"] for row in rows if not row["eligible_corpus_documents"]]
        raise ValueError(f"Brakuje tekstu opublikowanego przed zdarzeniami: {missing}")
    buffer = io.StringIO(newline="")
    writer = csv.DictWriter(buffer, fieldnames=list(rows[0]), lineterminator="\n", quoting=csv.QUOTE_ALL)
    writer.writeheader()
    writer.writerows({key: spreadsheet_safe(value) for key, value in row.items()} for row in rows)
    output.mkdir(parents=True, exist_ok=True)
    write_text(target, "\ufeff" + buffer.getvalue())
    write_text(output / "candidates_review_workbench.md", render_markdown(rows, stats))
    return stats


def summarize(rows):
    return {
        "candidates": len(rows),
        "manual_review_required": sum(row["manual_review_required"] == "true" for row in rows),
        "registered_decisions": sum(row["review_status_in_registry"] in {"include", "exclude"} for row in rows),
        "with_full_espi": sum(bool(row["espi_text"]) for row in rows),
        "with_local_attachments": sum(any(item["file"] and item["status"] != "missing_local_file"
                                          for item in json.loads(row["attachments"] or "[]")) for row in rows),
        "with_prior_espi_links": sum(bool(row["prior_espi_references"]) for row in rows),
        "with_same_day_candidate": sum(bool(row["same_issuer_day_candidate_ids"]) for row in rows),
        "with_money_mentions": sum(bool(row["money_mentions"]) for row in rows),
        "with_date_mentions": sum(bool(row["date_mentions"]) for row in rows),
        "with_eligible_periodic_text": sum(bool(row["eligible_corpus_documents"]) for row in rows),
        "with_newer_periodic_report": sum(row["no_newer_periodic_report"].lower() == "false" for row in rows),
        "periodic_evidence": dict(Counter(row["periodic_evidence_kind"] for row in rows)),
        "suggested_decision_types": dict(Counter(row["suggested_decision_type"] for row in rows)),
    }


def render_markdown(rows, stats):
    lines = [
        "# Arkusz weryfikacji kandydatów ESPI", "",
        f"Arkusz obejmuje {stats['candidates']} kandydatów. Każdy wiersz wymaga ręcznej decyzji. "
        f"W rejestrze odnotowano już {stats['registered_decisions']} decyzje pilotażowe.",
        "",
        f"Pełne treści ESPI są dostępne dla {stats['with_full_espi']} pozycji. "
        f"Lokalne pliki załączników dotyczą {stats['with_local_attachments']} pozycji, "
        f"a odsyłacze do wcześniejszych ESPI dotyczą {stats['with_prior_espi_links']} pozycji.",
        "",
        f"Tekst raportu okresowego opublikowanego przed zdarzeniem jest dostępny dla "
        f"{stats['with_eligible_periodic_text']} pozycji. Fragment z nazwą projektu znaleziono dla "
        f"{stats['periodic_evidence'].get('named_project', 0)} pozycji, a ogólny kontekst CAPEX "
        f"dla {stats['periodic_evidence'].get('general_capex_context', 0)} pozycji.",
        "",
        f"W {stats['with_newer_periodic_report']} pozycjach po przypisanym raporcie, a przed zdarzeniem ESPI "
        "ukazał się nowszy raport okresowy. Identyfikatory są podane w kolumnie `newer_periodic_report_ids`.",
        "",
        "Kwoty i terminy mają cytat i lokalizator źródła. Sugestie rodzaju decyzji oraz "
        "wskazania rodzaju kwoty wymagają potwierdzenia przez badacza. Wcześniejsze "
        "komunikaty są kandydatami do ustalenia planu bazowego.",
        "",
        "[Pełny arkusz CSV](candidates_review_workbench.csv)", "",
    ]
    current = None
    evidence_labels = {
        "named_project": "fragment z nazwą projektu",
        "general_capex_context": "ogólny kontekst CAPEX",
        "no_match": "brak dopasowanego fragmentu",
        "no_eligible_text": "oczekuje na tekst raportu",
    }
    for row in rows:
        if row["ticker"] != current:
            current = row["ticker"]
            lines += ["", f"## {current}", ""]
        title = re.sub(r"([\\\[\]_*<>])", r"\\\1", preview(row["title"]))
        newer = f" · nowszy raport {row['newer_periodic_report_ids']}" if row["newer_periodic_report_ids"] else ""
        lines.append(f"- **{row['event_id']}** · {row['event_date']} · {title}. "
                     f"{row['reference_report_id']} · {evidence_labels[row['periodic_evidence_kind']]}{newer}.")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=PROCESSED / "corpus" / "report_manifest.csv")
    parser.add_argument("--output-dir", type=Path, default=DATA_ROOT / "staging")
    parser.add_argument("--allow-incomplete", action="store_true", help="Allow a preview before the corpus is complete.")
    args = parser.parse_args()
    print(json.dumps(build(args.manifest, args.output_dir, allow_incomplete=args.allow_incomplete), ensure_ascii=False))


if __name__ == "__main__":
    main()
