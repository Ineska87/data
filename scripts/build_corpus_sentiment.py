#!/usr/bin/env python3
"""MVP corpus + dictionary sentiment on management-board texts (PL).

Scope (checklist §7 MVP — lists / sprawozdania zarządu, not full NLP on everything)
---------------------------------------------------------------------------------
1. Discover PDFs: ``*sprawozdanie-zarzadu*.pdf`` under ``data/raw/reports/{TICKER}/``
   plus PKN CEO/letter and selected PKN ``*sprawozdanie*.pdf`` when no SZ file.
2. Extract text with PyMuPDF (fitz).
3. Score with Polish adaptation of Loughran–McDonald style lists:
   positive / negative / uncertainty / certainty.
4. Metrics per document: TONE_MGR, UNCERTAINTY, CERTAINTY, READABILITY (proxy).
5. Aggregate to ticker × year × quarter → merge-ready table.

Outputs
-------
- data/processed/corpus/manifest.csv
- data/processed/corpus/corpus_docs.parquet (+ .csv)
- data/processed/corpus/texts/*.txt  (extracted plain text)
- data/processed/sentiment/doc_scores.parquet
- data/processed/sentiment/sentiment_quarterly.parquet (+ .csv)
- data/processed/sentiment/dictionary_pl_lm.md
- data/processed/sentiment/codebook.md
"""

from __future__ import annotations

import json
import re
import unicodedata
from collections import defaultdict
from pathlib import Path

import numpy as np
import pandas as pd

try:
    import fitz  # PyMuPDF
except ImportError as e:
    raise SystemExit("PyMuPDF (fitz) required: pip install pymupdf") from e

from data_paths import DATA_ROOT, LEGACY, load_study_scope
from investment_sentiment import (
    AR_PACKAGE, BASELINE_ARCHIVE, ORLEN_PILOT_PACKAGES, build_current_corpus, read_management_archive, read_orlen_archive,
)

ROOT = DATA_ROOT.parent
REPORTS = DATA_ROOT / "raw" / "reports"
CORPUS = LEGACY / "processed" / "corpus"
SENT = LEGACY / "processed" / "sentiment"
TEXTS = CORPUS / "texts"

TICKERS = ["PKN", "PGE", "TPE", "ENA", "ZEP", "UNT", "JSW"]

# period → calendar quarter for panel join
PERIOD_Q = {"Q1": 1, "H1": 2, "Q2": 2, "Q3": 3, "Q4": 4, "AR": 4}

# ---------------------------------------------------------------------------
# Polish LM-style dictionary (finance / energy corporate prose)
# Lists are stems/forms matched after simple normalization; multiword phrases
# checked on joined text. NOT a machine translation of LM — adapted for PL IR.
# ---------------------------------------------------------------------------
POS = {
    "wzrost", "wzrosn", "rosn", "rosną", "rosnący", "rosnące", "przyrost",
    "zysk", "zyski", "zyskown", "rentown", "dochod", "dochód", "dochodow",
    "sukces", "udany", "udane", "udanym", "powodzen",
    "popraw", "poprawa", "poprawy", "poprawie", "ulepsz", "optymaliz",
    "rekord", "rekordow", "najlepsz", "wiodac", "wiodąc", "lider",
    "efektywn", "efektywno", "produktywn", "oszczedn", "oszczędn",
    "rozwoj", "rozwój", "rozwoju", "rozwojow", "innowac", "innowacyj",
    "szansa", "szanse", "szansę", "mozliwosc", "możliwość", "możliwości", "potencjal", "potencjał",
    "stabiln", "stabiliz", "umocn", "wzmocn", "wzmocnienie", "wzmocnienia",
    "synerg", "integrac", "konsolidac", "transformac", "modernizac",
    "inwestycj", "inwestowan", "rozszerz", "ekspans",
    "satysfakc", "zaufan", "wiarygodn", "przejrzyst", "transparent",
    "bezpiecz", "niezawodn", "odpornos", "odporność", "resilient",
    "zielon", "dekarbon", "niskoweglow", "oze", "odnawialn", "emisyjnosc",
    "dywidend", "wypłat", "wyplat", "akcjonariusz",  # positive framing often
    "osiagn", "osiąg", "zrealizow", "zrealizowani", "zrealizowano",
    "przekrocz", "nadwyzk", "nadwyżk", "nadwyzka", "nadwyżka",
    "pozytywn", "korzystn", "korzystny", "korzystne", "korzystna",
    "solidn", "mocn", "siln", "dynamiczn", "ambitn",
    "postep", "postęp", "postępu", "przyspiesz",
    "oszczednosc", "oszczędność", "redukcja_koszt",  # phrase handled separate
    "marza", "marża", "marzy", "marż", "ebitda",
    "wzmacnia", "umacnia", "poprawia", "rozwija", "buduje",
}

NEG = {
    "strata", "straty", "stracie", "stratę", "stratn", "deficyt", "deficytu",
    "spadek", "spadku", "spadki", "spadk", "obnizen", "obniżen", "obnizk", "obniżk",
    "pogorszen", "pogorszy", "pogorszenie", "pogorszenia",
    "utrata", "utraty", "utracie", "utratę", "odpis", "odpisy", "odpisow", "odpisów", "impairment",
    "kryzys", "kryzysu", "kryzysow", "recesj", "turbulenc",
    "opoznien", "opóźnien", "opoznion", "opóźnion", "przekroczenie_termin",
    "kara", "kary", "karze", "sankcj", "grzywn", "postepowanie_sadow",
    "negatywn", "niekorzystn", "szkodliw", "zagrozen", "zagrożen", "grozb", "groźb",
    "trudnos", "trudność", "trudności", "problem", "problemy", "problemem",
    "awari", "awaria", "awarii", "wypadek", "incydent", "zaklocen", "zakłócen",
    "likwidac", "restrukturyzac", "zwolnien", "zwolnienia", "cięcie", "ciecia", "cięcia",
    "zadluzen", "zadłużen", "niewyplacaln", "niewypłacaln", "bankruct", "upadlosc", "upadłość",
    "słab", "slab", "słaby", "slaby", "słabe", "slabe", "slaba", "słaba",
    "nadmiern", "przeszacow", "niedoszacow", "niepowodzen", "porazk", "porażk",
    "rezygnac", "anulow", "wstrzyman", "zawiesz", "odstapien", "odstąpien",
    "szkod", "szkoda", "szkody", "roszczen", "pozew", "pozwy", "spór", "spor", "spory",
    "wyciek", "skazen", "skażen", "zanieczyszcz",
    "korupc", "naduzyc", "nadużyc", "nieprawidlow", "nieprawidł",
    "utraty_wartosci", "write-off", "writeoff",
}

# uncertainty (LM: modal / vague / risk language)
UNC = {
    "niepew", "niepewnosc", "niepewność", "niepewnosci", "niepewności",
    "ryzyko", "ryzyka", "ryzyku", "ryzykiem", "ryzykown", "ryzyk",
    "moze", "może", "moga", "mogą", "mozliw", "możliw", "ewentualn",
    "prawdopodobn", "szacunk", "szacuje", "szacowan", "przybliz", "przybliż",
    "w_zaleznosci", "zalezy", "zależy", "zalezne", "zależne", "warunkow", "warunków",
    "trudno_przewidziec", "trudno_ocenic", "nieprzewidywaln",
    "wahania", "zmiennosc", "zmienność", "zmiennosci", "zmienności", "fluktuac",
    "potencjaln", "potencjalnie", "hipotetyczn", "orientacyjn",
    "oczekuje", "oczekiwan", "prognoz", "prognoza", "prognozy", "scenariusz",
    "niejasn", "nieokreslon", "nieokreślon", "niezdefiniow",
    "moze_wplynac", "może_wpłynąć", "istnieje_ryzyko",
    "w_razie", "jesli", "jeśli", "jezeli", "jeżeli", "o_ile",
    "przyblizony", "przybliżony", "okolo", "około", "mniej_wiecej",
    "nie_mozna_wykluczyc", "nie_można_wykluczyć",
    "niepewnosci", "uncertainty", "risk",
}

CER = {
    "pewn", "pewny", "pewna", "pewne", "pewnosc", "pewność", "pewnie",
    "jednoznacz", "bez_watpienia", "bez_wątpienia", "niewatpliwie", "niewątpliwie",
    "potwierdz", "potwierdzamy", "potwierdzono", "gwarant", "zapewnia", "zapewniamy",
    "zawsze", "niezmiennie", "stal", "stały", "stala", "stała", "stale", "stałe",
    "ostateczn", "definitywn", "rozstrzygn", "zamkniety", "zamknięty",
    "zdecydowan", "zdecydowanie", "wyraznie", "wyraźnie", "jasno",
    "zobowiaz", "zobowiąz", "zobowiazujemy", "zobowiązujemy", "zobowiazanie",
    "realizujemy", "realizujemy_plan", "wedlug_planu", "zgodnie_z_planem",
    "niepodwazaln", "niepodważaln", "oczywist", "bezsporny", "bezspornie",
}


def strip_diacritics(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    return "".join(c for c in s if not unicodedata.combining(c))


def normalize_text(text: str) -> str:
    t = text.replace("\u00a0", " ").replace("\r", "\n")
    t = re.sub(r"-\n(?=\w)", "", t)  # hyphen line-break
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def tokenize(text: str) -> list[str]:
    t = strip_diacritics(text.lower())
    # keep letters and digits; split
    return re.findall(r"[a-z0-9]+", t)


def word_hits(tokens: list[str], lexicon: set[str]) -> int:
    """Count tokens that start with any lexicon stem (min stem len 4) or exact match."""
    n = 0
    # pre-sort stems by length desc for greedy-ish match
    stems = sorted(lexicon, key=len, reverse=True)
    exact = {s for s in stems if len(s) < 4}
    long = [s for s in stems if len(s) >= 4]
    for tok in tokens:
        if tok in exact or tok in lexicon:
            n += 1
            continue
        for st in long:
            if tok.startswith(st) or st.startswith(tok) and len(tok) >= 4:
                n += 1
                break
    return n


def syllable_proxy(word: str) -> int:
    w = strip_diacritics(word.lower())
    groups = re.findall(r"[aeiouy]+", w)
    return max(1, len(groups))


def readability_proxy(text: str, tokens: list[str]) -> float:
    """Simple FOG-like: 0.4 * (ASL + % long words). Higher = harder."""
    sentences = re.split(r"[.!?…]+", text)
    sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
    if not sentences or not tokens:
        return np.nan
    asl = len(tokens) / max(len(sentences), 1)
    long_w = sum(1 for t in tokens if syllable_proxy(t) >= 4)
    pct_long = 100.0 * long_w / len(tokens)
    return 0.4 * (asl + pct_long)


def score_text(text: str) -> dict:
    text = normalize_text(text)
    tokens = tokenize(text)
    n = len(tokens)
    if n < 50:
        return {
            "n_words": n,
            "n_pos": 0,
            "n_neg": 0,
            "n_unc": 0,
            "n_cer": 0,
            "TONE_MGR": np.nan,
            "UNCERTAINTY": np.nan,
            "CERTAINTY": np.nan,
            "READABILITY": np.nan,
            "pos_share": np.nan,
            "neg_share": np.nan,
        }
    # normalize lexicon once without diacritics
    pos_l = {strip_diacritics(x) for x in POS}
    neg_l = {strip_diacritics(x) for x in NEG}
    unc_l = {strip_diacritics(x) for x in UNC}
    cer_l = {strip_diacritics(x) for x in CER}

    n_pos = word_hits(tokens, pos_l)
    n_neg = word_hits(tokens, neg_l)
    n_unc = word_hits(tokens, unc_l)
    n_cer = word_hits(tokens, cer_l)

    tone = (n_pos - n_neg) / n
    unc = n_unc / n
    cer = n_cer / n
    return {
        "n_words": n,
        "n_pos": n_pos,
        "n_neg": n_neg,
        "n_unc": n_unc,
        "n_cer": n_cer,
        "TONE_MGR": tone,
        "UNCERTAINTY": unc,
        "CERTAINTY": cer,
        "READABILITY": readability_proxy(text, tokens),
        "pos_share": n_pos / n,
        "neg_share": n_neg / n,
    }


# ---------------------------------------------------------------------------
# Discovery + extraction
# ---------------------------------------------------------------------------
FNAME_RE = re.compile(
    r"^(?P<ticker>[A-Z]+)_(?P<year>\d{4})_(?P<period>AR|Q1|Q2|H1|Q3|Q4)_(?P<kind>.+)\.(?:pdf|zip|7z|xhtml|html|htm)$",
    re.I,
)


def discover_docs(tickers=TICKERS, first_year: int = 2020, last_year: int = 2025) -> list[dict]:
    docs = []
    for ticker in tickers:
        tdir = REPORTS / ticker
        if not tdir.is_dir():
            continue
        for p in sorted(tdir.iterdir()):
            if not p.is_file() or not (
                p.suffix.lower() == ".pdf" or AR_PACKAGE.fullmatch(p.name) or p.name in ORLEN_PILOT_PACKAGES
                or BASELINE_ARCHIVE.fullmatch(p.name)
            ):
                continue
            m = FNAME_RE.match(p.name)
            if not m:
                continue
            kind = m.group("kind").lower()
            period = m.group("period").upper()
            year = int(m.group("year"))
            if not first_year <= year <= last_year:
                continue

            doc_type = None
            priority = 99
            if "sprawozdanie-zarzadu" in kind or "sprawozdanie_zarzadu" in kind:
                doc_type = "sprawozdanie_zarzadu"
                priority = 1
            elif year == 2019 and kind in {"komentarz-zarzadu", "pozostale-informacje", "sprawozdanie-pozostale-informacje"}:
                doc_type = "periodic_management_comment"
                priority = 1
            elif "letter" in kind or "list" in kind:
                doc_type = "letter_ceo"
                priority = 2
            elif ticker == "PKN" and kind in ("sprawozdanie", "raport-zintegrowany", "sprawozdanie-zarzadu"):
                # PKN often has no separate SZ filename
                doc_type = "pkn_sprawozdanie_or_integrated"
                priority = 3
            elif ticker == "TPE" and kind == "sprawozdanie":
                # TPE quarterly/H1 management-ish report PDFs (AR skonsolidowany often is 7z misnamed)
                doc_type = "tpe_sprawozdanie"
                priority = 2
            elif ticker == "TPE" and "skonsolidowany" in kind and period == "AR":
                # often not a real PDF (7z payload) — lowest priority, may fail open
                doc_type = "tpe_ar_package"
                priority = 5
            elif year == 2019 and kind in {"sprawozdanie", "skonsolidowany"}:
                doc_type = "periodic_consolidated"
                priority = 3
            else:
                continue

            docs.append(
                {
                    "ticker": ticker,
                    "year": year,
                    "period": period,
                    "quarter": PERIOD_Q.get(period),
                    "doc_type": doc_type,
                    "priority": priority,
                    "path": str(p.relative_to(ROOT)).replace("\\", "/"),
                    "filename": p.name,
                    "abs_path": str(p),
                }
            )

    # keep all SZ/letters (prio 1–2); for prio 3–4 only if no prio≤2 in same ticker-year-period
    df = pd.DataFrame(docs)
    if df.empty:
        return []
    keep: list[dict] = []
    for (_, _, _), g in df.groupby(["ticker", "year", "period"]):
        g = g.sort_values("priority")
        primary = g[g["priority"] <= 2]
        if len(primary):
            keep.extend(primary.to_dict("records"))
        else:
            keep.append(g.iloc[0].to_dict())
    seen: set[str] = set()
    out: list[dict] = []
    for r in keep:
        if r["abs_path"] in seen:
            continue
        seen.add(r["abs_path"])
        out.append(r)
    return out


def discover_corpus_docs(scope: dict) -> list[dict]:
    """Choose local source packages before inspecting their individual documents."""
    study = set(scope["tickers"])
    validation = set(scope.get("possible_validation_tickers", []))
    start = int(scope["period"]["start"][:4])
    last = int(scope["period"]["end"][:4])
    receipts = REPORTS / "manifest_stage3_bundles.json"
    baseline = set(json.loads(receipts.read_text(encoding="utf-8"))["files"]) if receipts.exists() else set()
    groups = defaultdict(list)
    kinds = {
        "sprawozdanie": "periodic_statement",
        "skonsolidowany": "consolidated_package",
        "sprawozdanie-zarzadu": "management_report",
        "sprawozdanie-zarzadu-spolki": "management_report",
        "sprawozdanie-pozostale-informacje": "management_commentary",
        "pozostale-informacje": "management_commentary",
        "komentarz-zarzadu": "management_commentary",
        "prezentacja": "presentation",
        "letter-ceo": "ceo_letter",
        "raport-zintegrowany": "integrated_report",
    }
    formats = {".zip": 0, ".7z": 0, ".xbri": 0, ".xhtml": 1, ".pdf": 2, ".html": 3, ".htm": 3}
    for ticker in sorted(study | validation):
        folder = REPORTS / ticker
        if not folder.is_dir():
            continue
        for path in sorted(folder.iterdir()):
            match = FNAME_RE.fullmatch(path.name) if path.is_file() else None
            if not match:
                continue
            year = int(match["year"])
            relative = path.relative_to(DATA_ROOT).as_posix()
            kind = kinds.get(match["kind"].lower().replace("_", "-"))
            period = match["period"]
            if not kind or not (start <= year <= last or relative in baseline):
                continue
            if ticker in validation and period not in {"AR", "H1"}:
                continue
            key = ticker, year, period, kind
            groups[key].append(path)
    docs = []
    for (ticker, year, period, kind), files in groups.items():
        path = min(files, key=lambda item: (formats[item.suffix.lower()], item.name))
        docs.append({"ticker": ticker, "year": year, "period": period, "doc_type": kind,
                     "filename": path.name, "abs_path": str(path)})
    return sorted(docs, key=lambda row: (row["ticker"], row["year"], row["period"], row["filename"]))


def extract_pdf_text(path: Path | bytes, max_pages: int | None = None) -> tuple[str, int, str]:
    """Return (text, n_pages_used, status)."""
    try:
        doc = fitz.open(stream=path, filetype="pdf") if isinstance(path, bytes) else fitz.open(path)
    except Exception as e:
        return "", 0, f"open_fail:{type(e).__name__}"
    n_total = doc.page_count
    limit = n_total if max_pages is None else min(n_total, max_pages)
    parts = []
    for i in range(limit):
        try:
            parts.append(doc[i].get_text("text") or "")
        except Exception:
            continue
    doc.close()
    text = normalize_text("\n".join(parts))
    if len(text) < 100:
        return text, limit, "low_text"
    return text, limit, "ok"


def extract_letter_section(text: str) -> str | None:
    """Heuristic: cut Letter to shareholders / List Prezesa block if markers present."""
    patterns = [
        r"(list\s+(prezesa|prezeski|zarządu|zarzadu|do\s+akcjonariusz))",
        r"(szanowni\s+(państwo|akcjonariusze|akcjonariuszki))",
        r"(dear\s+shareholders)",
        r"(letter\s+from\s+the\s+(ceo|president|management))",
    ]
    low = strip_diacritics(text.lower())
    starts = []
    for pat in patterns:
        for m in re.finditer(pat, low, re.I):
            starts.append(m.start())
    if not starts:
        return None
    start = min(starts)
    # end at next major heading-ish gap or ~8000 chars
    chunk = text[start : start + 12000]
    return chunk if len(chunk) > 200 else None


def process_docs(docs: list[dict]) -> pd.DataFrame:
    TEXTS.mkdir(parents=True, exist_ok=True)
    rows = []
    for i, d in enumerate(docs, 1):
        path = Path(d["abs_path"])
        print(f"[{i}/{len(docs)}] {d['filename']} …", flush=True)
        # full SZ can be long; still extract all (cap 250 pages safety)
        max_pages = 250
        if d["doc_type"] in ("tpe_ar_package", "pkn_sprawozdanie_or_integrated"):
            max_pages = 40  # letter-ish front matter only for bulky packages
        if d["doc_type"] == "letter_ceo":
            max_pages = 30

        if AR_PACKAGE.fullmatch(path.name):
            text, _ = read_management_archive(path)
            n_pages, status = 0, "ok"
        elif path.name in ORLEN_PILOT_PACKAGES:
            text, _, status = read_orlen_archive(path, extract_pdf_text)
            n_pages = 0
        else:
            text, n_pages, status = extract_pdf_text(path, max_pages=max_pages)
        letter = extract_letter_section(text) if text else None
        use_text = letter if letter and len(letter) > 400 else text
        segment = "letter_section" if letter and use_text is letter else "full_or_front"

        # save text
        stem = Path(d["filename"]).stem
        txt_path = TEXTS / f"{stem}.txt"
        txt_path.write_text(use_text or "", encoding="utf-8")

        sc = score_text(use_text or "")
        row = {
            **{k: d[k] for k in ("ticker", "year", "period", "quarter", "doc_type", "priority", "path", "filename")},
            "n_pages_extracted": n_pages,
            "extract_status": status,
            "segment": segment,
            "text_path": str(txt_path.relative_to(ROOT)).replace("\\", "/"),
            "n_chars": len(use_text or ""),
            **sc,
        }
        rows.append(row)
        print(
            f"  status={status} pages={n_pages} words={sc['n_words']} "
            f"TONE={sc['TONE_MGR'] if sc['TONE_MGR']==sc['TONE_MGR'] else 'NA'} "
            f"seg={segment}",
            flush=True,
        )
    return pd.DataFrame(rows)


def aggregate_quarterly(doc_df: pd.DataFrame) -> pd.DataFrame:
    """Word-weighted average of scores to ticker×year×quarter."""
    d = doc_df[doc_df["extract_status"].isin(["ok", "low_text"])].copy()
    d = d[d["n_words"].fillna(0) >= 50]
    if d.empty:
        return pd.DataFrame()

    metrics = ["TONE_MGR", "UNCERTAINTY", "CERTAINTY", "READABILITY", "pos_share", "neg_share"]

    def wavg(g: pd.DataFrame) -> pd.Series:
        w = g["n_words"].astype(float)
        out = {"n_docs": len(g), "n_words_sum": int(w.sum())}
        for m in metrics:
            x = g[m].astype(float)
            mask = x.notna() & w.gt(0)
            if mask.any():
                out[m] = np.average(x[mask], weights=w[mask])
            else:
                out[m] = np.nan
        out["doc_types"] = ",".join(sorted(g["doc_type"].unique()))
        out["source_files"] = ";".join(g["filename"].tolist())
        return pd.Series(out)

    rows = []
    for keys, g in d.groupby(["ticker", "year", "quarter"]):
        s = wavg(g)
        rows.append({"ticker": keys[0], "year": int(keys[1]), "quarter": int(keys[2]), **s.to_dict()})
    return pd.DataFrame(rows)


def write_dictionary_md() -> None:
    lines = [
        "# Polski słownik tonu (adaptacja stylu Loughran–McDonald)",
        "",
        "MVP do scoringu `TONE_MGR` / `UNCERTAINTY` / `CERTAINTY` na tekstach zarządu.",
        "Listy **nie** są automatycznym tłumaczeniem LM EN — dobór pod PL prozę IR (energia/paliwa).",
        "",
        "Matching: normalizacja bez polskich znaków + prefix stem (min. 4 znaki).",
        "",
        f"## Positive (n={len(POS)})",
        "",
        ", ".join(sorted(POS)),
        "",
        f"## Negative (n={len(NEG)})",
        "",
        ", ".join(sorted(NEG)),
        "",
        f"## Uncertainty (n={len(UNC)})",
        "",
        ", ".join(sorted(UNC)),
        "",
        f"## Certainty (n={len(CER)})",
        "",
        ", ".join(sorted(CER)),
        "",
        "## Formuły",
        "",
        "- `TONE_MGR` = (n_pos − n_neg) / n_words",
        "- `UNCERTAINTY` = n_unc / n_words",
        "- `CERTAINTY` = n_cer / n_words",
        "- `READABILITY` = 0.4 × (średnia długość zdania + % słów z ≥4 „sylabami” proxy)",
        "",
        "Agregacja kwartalna: średnia ważona liczbą słów dokumentów w ticker×year×quarter.",
        "AR → Q4; H1 → Q2.",
        "",
    ]
    SENT.mkdir(parents=True, exist_ok=True)
    (SENT / "dictionary_pl_lm.md").write_text("\n".join(lines), encoding="utf-8")


def write_codebook(doc_df: pd.DataFrame, q_df: pd.DataFrame) -> None:
    text = f"""# Codebook — corpus & sentiment (MVP)

## Korpus

- Manifest: `processed/corpus/manifest.csv` ({len(doc_df)} dokumentów)
- Teksty: `processed/corpus/texts/*.txt`
- Tabela: `processed/corpus/corpus_docs.parquet`

| Pole | Opis |
|------|------|
| ticker, year, period, quarter | identyfikatory |
| doc_type | `sprawozdanie_zarzadu` / `letter_ceo` / `pkn_*` / `tpe_ar_package` |
| segment | `letter_section` jeśli wykryto list; inaczej `full_or_front` |
| n_words, extract_status | jakość ekstrakcji |

## Sentiment

- Per dokument: `processed/sentiment/doc_scores.parquet`
- Kwartalnie: `processed/sentiment/sentiment_quarterly.parquet` ({len(q_df)} wierszy)
- Słownik: `processed/sentiment/dictionary_pl_lm.md`

| Zmienna | Opis |
|---------|------|
| TONE_MGR | (pos−neg)/n — ton narracji zarządu |
| UNCERTAINTY | udział leksyki niepewności |
| CERTAINTY | udział leksyki pewności |
| READABILITY | proxy FOG (wyżej = trudniejszy tekst) |

## Ograniczenia MVP

- Bez ręcznej anotacji / precision-recall (checklist 7.2 otwarte).
- Brak `TONE_FUND_GAP` (wymaga niespodzianek EPS).
- Słownik regułowy — nie transformer.
- TPE/PKN: czasem pakiet AR zamiast osobnego SZ; front matter only.
- AR przypisane do Q4 (publikacja roczna).

## Skrypt

`data/scripts/build_corpus_sentiment.py`
"""
    (SENT / "codebook.md").write_text(text, encoding="utf-8")


def legacy_main() -> None:
    CORPUS.mkdir(parents=True, exist_ok=True)
    SENT.mkdir(parents=True, exist_ok=True)
    TEXTS.mkdir(parents=True, exist_ok=True)

    print("=== Discover ===", flush=True)
    docs = discover_docs()
    print(f"docs: {len(docs)}", flush=True)
    by_t = pd.Series([d["ticker"] for d in docs]).value_counts().to_dict()
    print("by ticker", by_t, flush=True)

    print("=== Extract + score ===", flush=True)
    doc_df = process_docs(docs)

    # manifest
    man_cols = [
        "ticker", "year", "period", "quarter", "doc_type", "segment",
        "path", "filename", "text_path", "n_pages_extracted", "n_words",
        "extract_status", "n_chars",
    ]
    man = doc_df[[c for c in man_cols if c in doc_df.columns]]
    man.to_csv(CORPUS / "manifest.csv", index=False)
    doc_df.to_parquet(CORPUS / "corpus_docs.parquet", index=False)
    doc_df.to_csv(CORPUS / "corpus_docs.csv", index=False)

    # scores only
    score_cols = [
        "ticker", "year", "period", "quarter", "doc_type", "filename", "segment",
        "n_words", "n_pos", "n_neg", "n_unc", "n_cer",
        "TONE_MGR", "UNCERTAINTY", "CERTAINTY", "READABILITY", "pos_share", "neg_share",
        "extract_status",
    ]
    scores = doc_df[[c for c in score_cols if c in doc_df.columns]]
    scores.to_parquet(SENT / "doc_scores.parquet", index=False)
    scores.to_csv(SENT / "doc_scores.csv", index=False)

    print("=== Quarterly aggregate ===", flush=True)
    q = aggregate_quarterly(doc_df)
    q.to_parquet(SENT / "sentiment_quarterly.parquet", index=False)
    q.to_csv(SENT / "sentiment_quarterly.csv", index=False)
    print(f"quarterly rows: {len(q)}", flush=True)
    if not q.empty:
        print(q.groupby("ticker").size().to_dict(), flush=True)
        print(q[["ticker", "year", "quarter", "TONE_MGR", "UNCERTAINTY", "n_docs"]].head(10).to_string(), flush=True)

    write_dictionary_md()
    write_codebook(doc_df, q)

    # coverage json
    cov = {
        "n_docs": int(len(doc_df)),
        "n_ok": int((doc_df["extract_status"] == "ok").sum()),
        "n_quarterly": int(len(q)),
        "by_ticker_docs": doc_df.groupby("ticker").size().to_dict(),
        "by_ticker_q": q.groupby("ticker").size().to_dict() if not q.empty else {},
        "mean_tone": float(q["TONE_MGR"].mean()) if not q.empty and q["TONE_MGR"].notna().any() else None,
    }
    (SENT / "coverage.json").write_text(json.dumps(cov, indent=2, ensure_ascii=False), encoding="utf-8")
    print("coverage", cov, flush=True)
    print("done", flush=True)


if __name__ == "__main__":
    from argparse import ArgumentParser

    parser = ArgumentParser(description="Build the investment-report corpus.")
    parser.add_argument("--legacy", action="store_true", help="Regenerate the old quarterly corpus and scores.")
    if parser.parse_args().legacy:
        legacy_main()
    else:
        scope = load_study_scope()
        build_current_corpus(discover_corpus_docs(scope), extract_pdf_text)
