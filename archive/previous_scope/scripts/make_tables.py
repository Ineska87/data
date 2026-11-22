"""
Generuje tabele akademickie gotowe do wklejenia do pracy magisterskiej.

Tabela 1: Parametry modelu rynkowego (beta, R², n per spółka)
Tabela 2: Główne wyniki CAR + testy statystyczne (kategoria × 3 okna)
Tabela 3: Analiza wrażliwości (pełna próba vs bez UNT/ZEP, okno [-5+5])

Wyjście:
  data/processed/tables/tabela1_model.csv
  data/processed/tables/tabela2_car_tests.csv
  data/processed/tables/tabela3_wrazliwosc.csv
  data/processed/tables/tabela2_car_tests.tex   (LaTeX)
  data/processed/tables/tabela3_wrazliwosc.tex  (LaTeX)
"""


from data_paths import LEGACY
import numpy as np
import pandas as pd

BASE = LEGACY
CAR_F   = BASE / "processed" / "car_results.parquet"
STAT_F  = BASE / "processed" / "stat_tests_results.csv"
OUT_DIR = BASE / "processed" / "tables"
OUT_DIR.mkdir(exist_ok=True)

car_df  = pd.read_parquet(CAR_F)
stat_df = pd.read_csv(STAT_F, encoding="utf-8-sig")

# Benchmark labels (PL)
BENCH_LABEL = {
    "WIG-energia": "WIG-Energia",
    "WIG-paliwa":  "WIG-Paliwa",
    "WIG":         "WIG",
    "WIG20":       "WIG20",
}

TICKER_FULL = {
    "PKN": "PKN Orlen",
    "PGE": "PGE",
    "TPE": "Tauron",
    "ENA": "Enea",
    "ZEP": "ZE PAK",
    "UNT": "Unimot",
    "JSW": "JSW",
    "LWB": "LW Bogdanka",
}

TICKER_TYPE = {
    "PKN": "państwowa",
    "PGE": "państwowa",
    "TPE": "państwowa",
    "ENA": "państwowa",
    "ZEP": "państwowa",
    "UNT": "prywatna",
    "JSW": "państwowa",
    "LWB": "państwowa",
}

# ── TABELA 1: Parametry modelu rynkowego ──────────────────────────────────────

sub55 = car_df[car_df["window"] == "[-5+5]"]
model_rows = []

for ticker in ["PKN", "PGE", "TPE", "ENA", "ZEP", "UNT", "JSW", "LWB"]:
    grp  = sub55[sub55["ticker"] == ticker]
    if grp.empty:
        continue
    bench = grp["benchmark"].iloc[0]
    beta  = grp["beta"].median()
    r2    = grp["r2"].median()
    n_est = grp["n_est"].median()
    n_ev  = grp["event_id"].nunique()

    # Ocena jakości dopasowania
    if r2 >= 0.70:
        quality = "doskonały"
    elif r2 >= 0.40:
        quality = "dobry"
    elif r2 >= 0.10:
        quality = "słaby"
    else:
        quality = "bardzo słaby"

    model_rows.append({
        "Spółka":        TICKER_FULL[ticker],
        "Typ własności": TICKER_TYPE[ticker],
        "Benchmark":     BENCH_LABEL.get(bench, bench),
        "β (mediana)":   round(beta, 3),
        "R² (mediana)":  round(r2, 3),
        "n_est (med.)":  int(n_est),
        "n_zdarzeń":     n_ev,
        "Ocena":         quality,
    })

t1 = pd.DataFrame(model_rows)
t1.to_csv(OUT_DIR / "tabela1_model.csv", index=False, encoding="utf-8-sig")

print("=" * 70)
print("TABELA 1: Parametry modelu rynkowego")
print("=" * 70)
print(t1.to_string(index=False))


# ── TABELA 2: Główne wyniki CAR + testy ───────────────────────────────────────
# Układ: kategoria × okno [-1+1] / [-3+3] / [-5+5]
# Kolumny per okno: CAR%, t_BMP, p_BMP (gwiazdki), p(>0)%

MAIN_WINDOWS = ["[-1+1]", "[-3+3]", "[-5+5]"]

# Kolejność kategorii (od najistotniejszych wyników)
CAT_ORDER = [
    "Rating/rekomendacja",
    "Dywidenda",
    "Transakcje M&A",
    "Walne zgromadzenie",
    "Regulacyjne/prawne",
    "Wyniki finansowe",
    "Akcjonariat/progi",
    "Umowy/kontrakty",
    "Emisja/finansowanie",
    "Zmiany personalne",
    "Inne",
]

full_stat = stat_df[stat_df["sample"] == "Pełna próba"]

t2_rows = []
for cat in CAT_ORDER:
    row = {"Kategoria": cat}
    for win in MAIN_WINDOWS:
        sub = full_stat[(full_stat["category"] == cat) & (full_stat["window"] == win)]
        if sub.empty:
            row[f"n_{win}"]     = ""
            row[f"CAR_{win}"]   = ""
            row[f"t_BMP_{win}"] = ""
            row[f"p_BMP_{win}"] = ""
            row[f"ppos_{win}"]  = ""
        else:
            r = sub.iloc[0]
            sig = r["sig_bmp"] if pd.notna(r["sig_bmp"]) else ""
            row[f"n_{win}"]     = int(r["n"]) if pd.notna(r["n"]) else ""
            row[f"CAR_{win}"]   = f"{r['mean_car_pct']:+.3f}%"
            row[f"t_BMP_{win}"] = f"{r['t_bmp']:.3f}"
            row[f"p_BMP_{win}"] = f"{r['p_bmp']:.4f}{sig}"
            row[f"ppos_{win}"]  = f"{r['prop_pos_pct']:.0f}%"
    t2_rows.append(row)

t2 = pd.DataFrame(t2_rows)
t2.to_csv(OUT_DIR / "tabela2_car_tests.csv", index=False, encoding="utf-8-sig")

print("\n\n" + "=" * 70)
print("TABELA 2: Wyniki CAR + BMP test per kategoria (pełna próba)")
print("=" * 70)
for _, r in t2.iterrows():
    print(f"\n  {r['Kategoria']}")
    for win in MAIN_WINDOWS:
        n   = r.get(f"n_{win}", "")
        car = r.get(f"CAR_{win}", "")
        t   = r.get(f"t_BMP_{win}", "")
        p   = r.get(f"p_BMP_{win}", "")
        pp  = r.get(f"ppos_{win}", "")
        if car:
            print(f"    {win:<12}  n={n:>4}  CAR={car:>9}  t={t:>7}  p={p:<12}  p(>0)={pp}")


# ── LaTeX: Tabela 2 ───────────────────────────────────────────────────────────

def tex_escape(s):
    return str(s).replace("%", r"\%").replace("&", r"\&").replace("_", r"\_")

def build_latex_t2(t2_df, windows):
    ncols = 1 + len(windows) * 4   # kategoria + n/CAR/t_BMP/p_BMP per okno

    header_top  = r"\begin{table}[htbp]" + "\n"
    header_top += r"\centering" + "\n"
    header_top += r"\footnotesize" + "\n"
    header_top += (r"\caption{Skumulowane nieprawidłowe stopy zwrotu (CAR) "
                   r"w wybranych oknach zdarzeń — test BMP}" + "\n")
    header_top += r"\label{tab:car_bmp}" + "\n"
    header_top += r"\begin{tabular}{l" + "rrrr" * len(windows) + "}\n"
    header_top += r"\toprule" + "\n"

    # Wiersz 1: okna (multicolumn)
    hrow1 = "Kategoria"
    for win in windows:
        label = win.replace("[", "$[$").replace("]", "$]$").replace("+", "$+$")
        hrow1 += f" & \\multicolumn{{4}}{{c}}{{{label}}}"
    hrow1 += r" \\" + "\n"
    header_top += hrow1
    header_top += r"\cmidrule(lr){2-5}" if len(windows) == 1 else ""
    for i, _ in enumerate(windows):
        start = 2 + i * 4
        header_top += f"\\cmidrule(lr){{{start}-{start+3}}}"
    header_top += "\n"

    # Wiersz 2: podkolumny
    hrow2 = ""
    for _ in windows:
        hrow2 += " & $n$ & CAR (\\%) & $t_{BMP}$ & $p$"
    hrow2 += r" \\" + "\n"
    header_top += hrow2
    header_top += r"\midrule" + "\n"

    body = ""
    for _, row in t2_df.iterrows():
        line = tex_escape(row["Kategoria"])
        for win in windows:
            n   = row.get(f"n_{win}",   "")
            car = row.get(f"CAR_{win}", "")
            t   = row.get(f"t_BMP_{win}", "")
            p   = row.get(f"p_BMP_{win}", "")
            # gwiazdki → bold
            p_str = str(p)
            for stars in ["***", "**", "*"]:
                if p_str.endswith(stars):
                    num = p_str[:-len(stars)]
                    p_str = f"{num}\\textbf{{{stars}}}"
                    break
            line += f" & {n} & {tex_escape(car)} & {tex_escape(t)} & {p_str}"
        body += line + r" \\" + "\n"

    footer  = r"\bottomrule" + "\n"
    footer += r"\end{tabular}" + "\n"
    footer += r"\begin{tablenotes}" + "\n"
    footer += (r"\small \item \textit{Uwagi:} "
               r"CAR obliczone metodą modelu rynkowego OLS. "
               r"$t_{BMP}$ — test Boehmera, Musumeciego i Pouslena (1991). "
               r"Gwiazdki: *** $p<0{,}01$; ** $p<0{,}05$; * $p<0{,}10$. "
               r"Próba: 8 spółek sektora energetyczno-paliwowego GPW, 2019–2025." + "\n")
    footer += r"\end{tablenotes}" + "\n"
    footer += r"\end{table}" + "\n"

    return header_top + body + footer


tex2 = build_latex_t2(t2, MAIN_WINDOWS)
(OUT_DIR / "tabela2_car_tests.tex").write_text(tex2, encoding="utf-8")


# ── TABELA 3: Analiza wrażliwości ─────────────────────────────────────────────
# Okno [-5+5], kategorie z >=3 zdarzeniami, 4 próbki

WIN55 = "[-5+5]"
sub55_stat = stat_df[stat_df["window"] == WIN55]

SAMPLE_ORDER = ["Pełna próba", "Bez UNT", "Bez ZEP", "Bez UNT+ZEP"]
SAMPLE_SHORT = {
    "Pełna próba":  "Pełna (n=8)",
    "Bez UNT":      "Bez UNT (n=7)",
    "Bez ZEP":      "Bez ZEP (n=7)",
    "Bez UNT+ZEP":  "Bez UNT+ZEP (n=6)",
}

# Kategorie dostępne w pełnej próbie
cats_available = (sub55_stat[sub55_stat["sample"] == "Pełna próba"]
                  .query("n >= 3")
                  ["category"]
                  .unique()
                  .tolist())
cats_sorted = [c for c in CAT_ORDER if c in cats_available]

t3_rows = []
for cat in cats_sorted:
    row = {"Kategoria": cat}
    for samp in SAMPLE_ORDER:
        sub = sub55_stat[(sub55_stat["sample"] == samp) & (sub55_stat["category"] == cat)]
        key = SAMPLE_SHORT[samp]
        if sub.empty:
            row[f"n_{samp}"]   = ""
            row[f"CAR_{samp}"] = ""
            row[f"p_{samp}"]   = ""
        else:
            r   = sub.iloc[0]
            sig = r["sig_bmp"] if pd.notna(r["sig_bmp"]) else ""
            row[f"n_{samp}"]   = int(r["n"]) if pd.notna(r["n"]) else ""
            row[f"CAR_{samp}"] = f"{r['mean_car_pct']:+.3f}%"
            row[f"p_{samp}"]   = f"{r['p_bmp']:.4f}{sig}"
    t3_rows.append(row)

t3 = pd.DataFrame(t3_rows)
t3.to_csv(OUT_DIR / "tabela3_wrazliwosc.csv", index=False, encoding="utf-8-sig")

print("\n\n" + "=" * 70)
print("TABELA 3: Analiza wrażliwości — okno [-5+5]")
print("CAR% | p_BMP  dla 4 wariantów próby")
print("=" * 70)

header = f"  {'Kategoria':<28}"
for samp in SAMPLE_ORDER:
    header += f"  {SAMPLE_SHORT[samp]:<18}"
print(header)
print("  " + "─" * 100)

for _, row in t3.iterrows():
    line = f"  {row['Kategoria']:<28}"
    for samp in SAMPLE_ORDER:
        car = row.get(f"CAR_{samp}", "")
        p   = row.get(f"p_{samp}",   "")
        cell = f"{car} ({p})" if car else "—"
        line += f"  {cell:<18}"
    print(line)


# ── LaTeX: Tabela 3 ───────────────────────────────────────────────────────────

def build_latex_t3(t3_df):
    ns = len(SAMPLE_ORDER)
    tex  = r"\begin{table}[htbp]" + "\n"
    tex += r"\centering\footnotesize" + "\n"
    tex += (r"\caption{Analiza wrażliwości wyników CAR [-5,+5] — "
            r"wpływ wykluczenia spółek o niskim dopasowaniu modelu}" + "\n")
    tex += r"\label{tab:sensitivity}" + "\n"
    tex += r"\begin{tabular}{l" + "rr" * ns + "}\n"
    tex += r"\toprule" + "\n"

    hrow = "Kategoria"
    for samp in SAMPLE_ORDER:
        hrow += f" & \\multicolumn{{2}}{{c}}{{{tex_escape(SAMPLE_SHORT[samp])}}}"
    hrow += r" \\" + "\n"
    tex += hrow

    for i in range(ns):
        start = 2 + i * 2
        tex += f"\\cmidrule(lr){{{start}-{start+1}}}"
    tex += "\n"

    sub_hrow = ""
    for _ in SAMPLE_ORDER:
        sub_hrow += " & CAR (\\%) & $p_{BMP}$"
    sub_hrow += r" \\" + "\n"
    tex += sub_hrow
    tex += r"\midrule" + "\n"

    for _, row in t3_df.iterrows():
        line = tex_escape(row["Kategoria"])
        for samp in SAMPLE_ORDER:
            car = row.get(f"CAR_{samp}", "")
            p   = row.get(f"p_{samp}",   "")
            p_str = str(p)
            for stars in ["***", "**", "*"]:
                if p_str.endswith(stars):
                    num = p_str[:-len(stars)]
                    p_str = f"{num}\\textbf{{{stars}}}"
                    break
            c = tex_escape(car) if car else "—"
            line += f" & {c} & {p_str}"
        tex += line + r" \\" + "\n"

    tex += r"\bottomrule" + "\n"
    tex += r"\end{tabular}" + "\n"
    tex += r"\begin{tablenotes}" + "\n"
    tex += (r"\small \item \textit{Uwagi:} Okno zdarzenia $[-5,+5]$ dni sesyjnych. "
            r"$p_{BMP}$ — test Boehmera, Musumeciego i Pouslena (1991). "
            r"UNT ($R^2=0{,}081$) i ZEP ($R^2=0{,}086$) — spółki o niskim dopasowaniu "
            r"modelu rynkowego. *** $p<0{,}01$; ** $p<0{,}05$; * $p<0{,}10$." + "\n")
    tex += r"\end{tablenotes}" + "\n"
    tex += r"\end{table}" + "\n"
    return tex


tex3 = build_latex_t3(t3)
(OUT_DIR / "tabela3_wrazliwosc.tex").write_text(tex3, encoding="utf-8")

print("\n\n" + "=" * 70)
print("Zapisano:")
for f in sorted(OUT_DIR.iterdir()):
    print(f"  {f.name}")
print("=" * 70)
