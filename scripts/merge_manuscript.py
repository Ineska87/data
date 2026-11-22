"""Scal rozdziały ROZDZIAL_*.md + ABSTRACT → MAGISTERKA_SCALONA.md"""
from __future__ import annotations

import re

from data_paths import LEGACY

PROC = LEGACY / "processed"

CHAPTERS = [
    ("ABSTRACT.md", None),
    ("ROZDZIAL_Wstep.md", "Wstęp"),
    (
        "ROZDZIAL_1_Teoria_BCF.md",
        "Rozdział 1. Behawioralne finanse przedsiębiorstw jako rama analityczna",
    ),
    (
        "ROZDZIAL_2_Sektor_GPW.md",
        "Rozdział 2. Sektor energetyczno-paliwowy na GPW w latach 2020–2025",
    ),
    ("ROZDZIAL_Dane_i_metody.md", "Rozdział 3. Dane i metody badawcze"),
    (
        "ROZDZIAL_4_Case_studies.md",
        "Rozdział 4. Przejawy czynników behawioralnych w decyzjach strategicznych — wielokrotne studium przypadku",
    ),
    ("ROZDZIAL_Wyniki.md", "Rozdział 5. Wyniki badań empirycznych"),
    (
        "ROZDZIAL_Dyskusja.md",
        "Rozdział 6. Dyskusja wyników i weryfikacja hipotez",
    ),
    ("ROZDZIAL_Zakonczenie.md", "Zakończenie"),
]


def strip_author_notes(text: str) -> str:
    text = re.sub(
        r"\n## Nota dla autora[\s\S]*",
        "",
        text,
        flags=re.IGNORECASE,
    )
    text = re.sub(
        r"\n### Nota dla autora[\s\S]*",
        "",
        text,
        flags=re.IGNORECASE,
    )
    return text.rstrip() + "\n"


def strip_first_h1(text: str) -> str:
    lines = text.splitlines()
    out: list[str] = []
    skipped = False
    for line in lines:
        if not skipped and line.startswith("# "):
            skipped = True
            continue
        out.append(line)
    return "\n".join(out).lstrip("\n")


def main() -> None:
    parts: list[str] = []

    parts.append(
        """---
title: "Przejawy czynników behawioralnych w decyzjach inwestycyjno-finansowych wybranych spółek sektora energetyczno-paliwowego notowanych na GPW w latach 2020–2025"
type: magisterka-robocza
status: draft-scalone
note: "Scalenie z ROZDZIAL_*.md — ujednolicić numerację i bibliografię przed oddaniem."
---

# Przejawy czynników behawioralnych w decyzjach inwestycyjno-finansowych wybranych spółek sektora energetyczno-paliwowego notowanych na GPW w latach 2020–2025

**Praca magisterska (wersja robocza — plik scalony)**

Szkoła Główna Handlowa w Warszawie

*Dokument scalony z `data/archive/previous_scope/processed/ROZDZIAL_*.md` + streszczenie. W treści wyników mogą pozostać wewnętrzne numery sekcji z wersji roboczej (np. 4.x) — do ujednolicenia w Wordzie jako Rozdział 5.*

---

## Spis treści (roboczy)

1. Streszczenie
2. Wstęp
3. Rozdział 1 — Teoria BCF
4. Rozdział 2 — Sektor GPW 2020–2025
5. Rozdział 3 — Dane i metody
6. Rozdział 4 — Studia przypadku
7. Rozdział 5 — Wyniki empiryczne
8. Rozdział 6 — Dyskusja
9. Zakończenie

**Materiały poza plikiem (odsyłacze):** `MAPA_HIPOTEZ.md`, `METODOLOGIA_fragmenty_dane.md`, `tables/`, `plots/`, `case_studies/kalendarium_*.md`, `Bibliography/moje_pdfy/`

---

"""
    )

    # Abstract PL full
    abs_text = (PROC / "ABSTRACT.md").read_text(encoding="utf-8")
    m = re.search(
        r"## Streszczenie \(PL\) — wersja pełna[^\n]*\n+(.*?)(?=\n---\n|\n## Streszczenie \(PL\) — wersja krótka)",
        abs_text,
        re.DOTALL,
    )
    parts.append("# Streszczenie\n\n")
    if m:
        parts.append(m.group(1).strip() + "\n\n---\n\n")
    else:
        parts.append(strip_author_notes(abs_text) + "\n\n---\n\n")

    for fname, display_title in CHAPTERS:
        if fname == "ABSTRACT.md":
            continue
        path = PROC / fname
        if not path.exists():
            print("MISSING", fname)
            continue
        raw = strip_author_notes(path.read_text(encoding="utf-8"))
        body = strip_first_h1(raw)
        if display_title:
            parts.append(f"# {display_title}\n\n")
        parts.append(body)
        if not body.endswith("\n"):
            parts.append("\n")
        parts.append("\n\n---\n\n")
        print("OK", fname)

    parts.append(
        """# Aneksy i materiały robocze (odsyłacze)

| Materiał | Ścieżka |
|----------|---------|
| Mapa hipotez H1–H11 | `data/archive/previous_scope/processed/MAPA_HIPOTEZ.md` |
| Fragmenty metodologii | `data/archive/previous_scope/processed/METODOLOGIA_fragmenty_dane.md` |
| Tabele | `data/archive/previous_scope/processed/tables/` |
| Wykresy AAR | `data/archive/previous_scope/processed/plots/` |
| Kalendaria case | `data/archive/previous_scope/processed/case_studies/` |
| Bibliografia PDF | `Bibliography/moje_pdfy/` |
| Skrypty | `data/scripts/` |

---

*Koniec pliku scalonego. Przed oddaniem: (1) ujednolicić numerację sekcji, (2) skrócić powtórzenia CAR między R4 a R5, (3) dodać bibliografię i spis tabel/rysunków, (4) zweryfikować liczby NIK w PDF.*
"""
    )

    text = "".join(parts)
    text = re.sub(r"\n{4,}", "\n\n\n", text)
    out = PROC / "MAGISTERKA_SCALONA.md"
    out.write_text(text, encoding="utf-8")
    print("Wrote", out)
    print("lines", text.count("\n") + 1)
    print("KB", round(out.stat().st_size / 1024, 1))


if __name__ == "__main__":
    main()
