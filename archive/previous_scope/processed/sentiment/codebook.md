# Codebook — corpus & sentiment (MVP)

## Korpus

- Manifest: `processed/corpus/manifest.csv` (81 dokumentów)
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
- Kwartalnie: `processed/sentiment/sentiment_quarterly.parquet` (74 wierszy)
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
