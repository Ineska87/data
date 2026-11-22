"""
Krok 2: Testy statystyczne — event study.

Implementuje:
  - BMP test (Boehmer, Musumeci & Poulsen 1991) — parametryczny, cross-sectional
    Standaryzuje CAR przez odchylenie std z okna estymacji → odporny na
    heteroscedastyczność przekrojową.
  - Test znaku (H0: p(CAR > 0) = 0.5) — nieparametryczny
  - Bootstrap 95% CI dla małych kategorii (n < 20)
  - Analiza wrażliwości: pełna próba / bez UNT / bez ZEP / bez UNT+ZEP

Wyjście:
  data/processed/stat_tests_results.csv   — pełna tabela wyników
  data/processed/stat_tests_summary.txt   — czytelne podsumowanie
"""


from data_paths import LEGACY
import warnings
import numpy as np
import pandas as pd
from scipy import stats

warnings.filterwarnings("ignore")
np.random.seed(42)

BASE = LEGACY
CAR_F   = BASE / "processed" / "car_results.parquet"
OUT_DIR = BASE / "processed"

car_df = pd.read_parquet(CAR_F)

WINDOWS = ["[-1+1]", "[-3+3]", "[-5+5]", "[-10+10]"]

WINDOW_LEN = {
    "[-1+1]":    3,
    "[-3+3]":    7,
    "[-5+5]":   11,
    "[-10+10]": 21,
    "[-20+20]": 41,
}

LOW_FIT = {"UNT", "ZEP"}   # spółki z R² < 10%


# ── Funkcje testów ────────────────────────────────────────────────────────────

def bmp_test(cars, resid_sds, n_ests, window_len):
    """
    Boehmer, Musumeci & Poulsen (1991) cross-sectional test.

    SCAR_i = CAR_i / (σ_i × √(L + L²/L₁))
    θ_BMP  = mean(SCAR) / (std(SCAR) / √N)  ~ t(N-1)

    Parametry:
        cars      – lista wartości CAR
        resid_sds – lista σ_i (std reszt OLS z okna estymacji)
        n_ests    – lista L₁ (długości okna estymacji)
        window_len – L (długość okna zdarzenia)
    """
    L = window_len
    df = (pd.DataFrame({"car": cars, "resid_sd": resid_sds, "n_est": n_ests})
            .dropna())
    if len(df) < 2:
        return np.nan, np.nan, np.nan, 0

    L1    = df["n_est"].values
    sigma = df["resid_sd"].values

    denom = sigma * np.sqrt(L + L**2 / L1)
    # Zabezpieczenie: jeśli denom=0 (nie powinno się zdarzyć), pomijamy
    valid = denom > 0
    if valid.sum() < 2:
        return np.nan, np.nan, np.nan, int(valid.sum())

    scar      = df["car"].values[valid] / denom[valid]
    n         = len(scar)
    mean_scar = float(np.mean(scar))
    std_scar  = float(np.std(scar, ddof=1))

    if std_scar == 0:
        return float(df["car"].mean() * 100), np.nan, np.nan, n

    t_stat    = mean_scar / (std_scar / np.sqrt(n))
    p_val     = float(2 * stats.t.sf(abs(t_stat), df=n - 1))
    mean_car  = float(df["car"].mean() * 100)

    return mean_car, float(t_stat), p_val, n


def sign_test(cars):
    """
    Test znaku (H0: P(CAR > 0) = 0.5).

    W  = liczba dodatnich CAR
    Z  = (W - N/2) / √(N/4)  ~ N(0,1)

    Zwraca: (n_pos, prop_pos_pct, z_stat, p_two_sided, n)
    """
    vals = np.array([c for c in cars if not np.isnan(c)])
    n    = len(vals)
    if n < 2:
        return np.nan, np.nan, np.nan, np.nan, n

    n_pos = int((vals > 0).sum())
    prop  = n_pos / n
    z     = (n_pos - n * 0.5) / np.sqrt(n * 0.25)
    p     = float(2 * stats.norm.sf(abs(z)))

    return n_pos, round(prop * 100, 1), round(float(z), 4), p, n


def bootstrap_ci(cars, n_boot=5000, alpha=0.05):
    """Bootstrap 95% CI dla średniego CAR (w %)."""
    vals = np.array([c * 100 for c in cars if not np.isnan(c)])
    if len(vals) < 2:
        return np.nan, np.nan
    boots = [float(np.mean(np.random.choice(vals, size=len(vals), replace=True)))
             for _ in range(n_boot)]
    lo = float(np.percentile(boots, 100 * alpha / 2))
    hi = float(np.percentile(boots, 100 * (1 - alpha / 2)))
    return lo, hi


def sig_stars(p):
    if pd.isna(p):
        return ""
    if p < 0.01: return "***"
    if p < 0.05: return "**"
    if p < 0.10: return "*"
    return ""


# ── Próbki (pełna + wrażliwość) ───────────────────────────────────────────────

SAMPLES = {
    "Pełna próba":   car_df,
    "Bez UNT":       car_df[car_df["ticker"] != "UNT"],
    "Bez ZEP":       car_df[car_df["ticker"] != "ZEP"],
    "Bez UNT+ZEP":   car_df[~car_df["ticker"].isin(["UNT", "ZEP"])],
}

# ── Pętla główna ──────────────────────────────────────────────────────────────

RESULTS = []

for sample_name, df_s in SAMPLES.items():
    for window in WINDOWS:
        L       = WINDOW_LEN[window]
        sub_win = df_s[df_s["window"] == window].dropna(subset=["car"])

        # Tylko kategorie z min 3 zdarzeniami
        valid_cats = (sub_win.groupby("event_type_pl")["event_id"]
                      .nunique()
                      .loc[lambda x: x >= 3]
                      .index
                      .tolist())

        for cat in valid_cats:
            sub = sub_win[sub_win["event_type_pl"] == cat]

            mean_car, t_bmp, p_bmp, n_bmp = bmp_test(
                sub["car"].tolist(),
                sub["resid_sd"].tolist(),
                sub["n_est"].tolist(),
                L
            )
            n_pos, prop_pos, z_sign, p_sign, n_sign = sign_test(
                sub["car"].tolist()
            )

            # Bootstrap tylko dla małych grup
            ci_lo, ci_hi = np.nan, np.nan
            if n_bmp < 20:
                ci_lo, ci_hi = bootstrap_ci(sub["car"].tolist())

            RESULTS.append({
                "sample":        sample_name,
                "window":        window,
                "category":      cat,
                "n":             n_bmp,
                "mean_car_pct":  round(mean_car, 4) if not np.isnan(mean_car) else np.nan,
                "median_car_pct": round(sub["car"].median() * 100, 4),
                "t_bmp":         round(t_bmp,   4) if not np.isnan(t_bmp)   else np.nan,
                "p_bmp":         round(p_bmp,   4) if not np.isnan(p_bmp)   else np.nan,
                "sig_bmp":       sig_stars(p_bmp),
                "n_pos":         n_pos,
                "prop_pos_pct":  prop_pos,
                "z_sign":        round(z_sign,  4) if not np.isnan(z_sign)  else np.nan,
                "p_sign":        round(p_sign,  4) if not np.isnan(p_sign)  else np.nan,
                "sig_sign":      sig_stars(p_sign),
                "boot_ci_lo":    round(ci_lo, 4) if not np.isnan(ci_lo) else np.nan,
                "boot_ci_hi":    round(ci_hi, 4) if not np.isnan(ci_hi) else np.nan,
            })

results_df = pd.DataFrame(RESULTS)

# ── Wydruk: pełna próba, wszystkie okna ──────────────────────────────────────

lines = []

def L(s):
    lines.append(s)
    print(s)

L("=" * 108)
L("TESTY STATYSTYCZNE — EVENT STUDY  |  GPW 2019–2025  |  Sektor energetyczno-paliwowy")
L("BMP = Boehmer, Musumeci & Poulsen (1991) | SIGN = test znaku (H0: p=0.5)")
L("Gwiazdki: *** p<0.01  ** p<0.05  * p<0.10")
L("=" * 108)

for window in WINDOWS:
    sub_w = results_df[(results_df["sample"] == "Pełna próba") &
                       (results_df["window"]  == window)]

    L(f"\n{'─' * 108}")
    L(f"OKNO ZDARZENIA: {window}  (L = {WINDOW_LEN[window]} dni)")
    L(f"{'─' * 108}")
    L(f"  {'Kategoria':<26}  {'n':>4}  {'CAR%':>8}  {'med%':>8}  "
      f"{'t_BMP':>7}  {'p_BMP':>7}  {'':>3}  "
      f"{'p(>0)%':>7}  {'z_sign':>7}  {'p_sign':>7}  {'':>3}  {'Boot 95% CI':>20}")
    L(f"  {'─' * 102}")

    for _, row in sub_w.sort_values("mean_car_pct", ascending=False).iterrows():
        ci_str = ""
        if not pd.isna(row.get("boot_ci_lo")):
            ci_str = f"[{row['boot_ci_lo']:+.2f}%, {row['boot_ci_hi']:+.2f}%]"

        L(f"  {row['category']:<26}  {row['n']:4.0f}  "
          f"{row['mean_car_pct']:+7.3f}%  {row['median_car_pct']:+7.3f}%  "
          f"{row['t_bmp']:7.3f}  {row['p_bmp']:7.4f}  {row['sig_bmp']:>3}  "
          f"{row['prop_pos_pct']:6.1f}%  {row['z_sign']:7.3f}  "
          f"{row['p_sign']:7.4f}  {row['sig_sign']:>3}  {ci_str:<20}")

# ── Wydruk: wrażliwość (okno [-5+5]) ─────────────────────────────────────────

L("\n\n" + "=" * 108)
L("ANALIZA WRAŻLIWOŚCI — OKNO [-5+5]")
L("Czy wyniki zmieniają się po wykluczeniu spółek z niskim R² (UNT, ZEP)?")
L("=" * 108)

cats_55 = (results_df[(results_df["window"] == "[-5+5]") &
                       (results_df["sample"] == "Pełna próba")]
           ["category"]
           .unique()
           .tolist())

for cat in sorted(cats_55):
    sub_c = results_df[(results_df["window"] == "[-5+5]") &
                       (results_df["category"] == cat)]

    L(f"\n  {cat}")
    L(f"  {'Próba':<18}  {'n':>4}  {'CAR%':>8}  {'t_BMP':>7}  "
      f"{'p_BMP':>7}  {'':>3}  {'p(>0)%':>7}  {'z_sign':>7}")

    for _, row in sub_c.iterrows():
        L(f"  {row['sample']:<18}  {row['n']:4.0f}  "
          f"{row['mean_car_pct']:+7.3f}%  {row['t_bmp']:7.3f}  "
          f"{row['p_bmp']:7.4f}  {row['sig_bmp']:>3}  "
          f"{row['prop_pos_pct']:6.1f}%  {row['z_sign']:7.3f}")

# ── Zapis ─────────────────────────────────────────────────────────────────────

csv_out = OUT_DIR / "stat_tests_results.csv"
results_df.to_csv(csv_out, index=False, encoding="utf-8-sig")

txt_out = OUT_DIR / "stat_tests_summary.txt"
txt_out.write_text("\n".join(lines), encoding="utf-8")

print(f"\n\nZapisano:")
print(f"  {csv_out}  ({len(results_df)} wierszy)")
print(f"  {txt_out}")
