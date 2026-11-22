"""
Krok 1: Wykresy AAR (Average Abnormal Returns) w oknie [-10, +10].

Diagnostyka:
  - Skupienie reakcji rynku wokół t=0
  - Pre-event leakage (drift przed zdarzeniem)
  - Asymetria odpowiedzi
  - CAAR (Cumulative Average Abnormal Return) per kategoria

Wyjście: PNG do data/processed/plots/
"""


from data_paths import LEGACY
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")   # zapis do pliku bez GUI
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.gridspec as gridspec

warnings.filterwarnings("ignore")

BASE = LEGACY
AR_F    = BASE / "processed" / "ar_daily.parquet"
CAR_F   = BASE / "processed" / "car_results.parquet"
OUT_DIR = BASE / "processed" / "plots"
OUT_DIR.mkdir(exist_ok=True)

ar_df  = pd.read_parquet(AR_F)
car_df = pd.read_parquet(CAR_F)

# Mapa: event_id → (event_type, event_type_pl, ticker)
meta_cols = ["event_id", "event_type", "event_type_pl", "ticker"]
cat_map = (car_df[meta_cols]
           .drop_duplicates("event_id")
           .set_index("event_id"))

ar_df = ar_df.join(cat_map, on="event_id", rsuffix="_meta")

# Filtr: okno [-10..+10]
ar_win = ar_df[ar_df["rel_day"].between(-10, 10)].copy()

DAYS   = list(range(-10, 11))
MIN_N  = 10   # minimalna liczba zdarzeń

# Kolory per kategoria
COLORS = {
    "Wyniki finansowe":     "#1565C0",
    "Regulacyjne/prawne":   "#C62828",
    "Akcjonariat/progi":    "#E65100",
    "Dywidenda":            "#2E7D32",
    "Rating/rekomendacja":  "#6A1B9A",
    "M&A":                  "#00695C",
    "Emisja akcji/obligacji": "#4527A0",
    "Inne":                 "#546E7A",
}
DEFAULT_COLOR = "#546E7A"

# ── Helper: oblicz AAR i CI ────────────────────────────────────────────────────

def compute_aar(sub_df):
    """Zwraca DataFrame z kolumnami: rel_day, aar, ci_lo, ci_hi, n."""
    rows = []
    for d in DAYS:
        vals = sub_df[sub_df["rel_day"] == d]["ar"].dropna().values * 100  # w %
        n    = len(vals)
        if n == 0:
            rows.append({"rel_day": d, "aar": np.nan, "ci_lo": np.nan,
                         "ci_hi": np.nan, "n": 0})
        else:
            mean = float(np.mean(vals))
            se   = float(np.std(vals, ddof=1) / np.sqrt(n)) if n > 1 else 0.0
            rows.append({"rel_day": d, "aar": mean,
                         "ci_lo": mean - 1.96 * se,
                         "ci_hi": mean + 1.96 * se,
                         "n": n})
    return pd.DataFrame(rows).set_index("rel_day")


def plot_aar_category(cat, sub_df, n_events, out_path):
    color  = COLORS.get(cat, DEFAULT_COLOR)
    aar_df = compute_aar(sub_df)
    caar   = aar_df["aar"].cumsum()

    fig = plt.figure(figsize=(11, 7.5))
    gs  = gridspec.GridSpec(2, 1, figure=fig, hspace=0.12)
    ax1 = fig.add_subplot(gs[0])   # AAR daily
    ax2 = fig.add_subplot(gs[1])   # CAAR

    # ─── Panel górny: AAR ────────────────────────────────────────────────────
    ax1.bar(DAYS, aar_df["aar"], color=color, alpha=0.60, width=0.7, label="AAR")
    ax1.fill_between(DAYS,
                     aar_df["ci_lo"], aar_df["ci_hi"],
                     alpha=0.18, color=color, label="95% CI")
    ax1.axhline(0, color="black", linewidth=0.8, linestyle="--", alpha=0.7)
    ax1.axvline(0, color="#B71C1C", linewidth=1.5, linestyle=":", label="Day 0")
    ax1.set_ylabel("AAR (%)", fontsize=11)
    ax1.set_title(f"{cat}  —  n = {n_events} zdarzeń", fontsize=13, fontweight="bold")
    ax1.legend(fontsize=9, loc="upper left")
    ax1.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.2f%%"))
    ax1.grid(axis="y", alpha=0.25, linewidth=0.6)
    ax1.tick_params(labelbottom=False)

    # Oznacz t=−5, 0, +5
    for x_mark in [-5, 0, 5]:
        ax1.axvline(x_mark, color="grey", linewidth=0.5, linestyle="--", alpha=0.5)

    # ─── Panel dolny: CAAR ───────────────────────────────────────────────────
    caar_vals = caar.values
    positive  = caar_vals >= 0
    negative  = caar_vals < 0

    ax2.fill_between(DAYS, 0, caar_vals, where=positive,
                     color=color, alpha=0.35, interpolate=True)
    ax2.fill_between(DAYS, 0, caar_vals, where=negative,
                     color="#B71C1C", alpha=0.25, interpolate=True)
    ax2.plot(DAYS, caar_vals, color=color, linewidth=2,
             marker="o", markersize=4, label="CAAR")

    ax2.axhline(0, color="black", linewidth=0.8, linestyle="--", alpha=0.7)
    ax2.axvline(0, color="#B71C1C", linewidth=1.5, linestyle=":", label="Day 0")
    for x_mark in [-5, 0, 5]:
        ax2.axvline(x_mark, color="grey", linewidth=0.5, linestyle="--", alpha=0.5)

    # Oznacz końcowy CAAR
    final_caar = float(caar_vals[-1]) if len(caar_vals) > 0 else 0.0
    ax2.annotate(f"CAAR[+10] = {final_caar:+.3f}%",
                 xy=(10, final_caar),
                 xytext=(-3, final_caar + (0.05 if final_caar >= 0 else -0.05)),
                 fontsize=8.5, color=color, fontweight="bold",
                 arrowprops=dict(arrowstyle="-", color=color, lw=0.8))

    ax2.set_xlabel("Dzień względny (Day 0 = data zdarzenia)", fontsize=11)
    ax2.set_ylabel("CAAR (%)", fontsize=11)
    ax2.legend(fontsize=9, loc="upper left")
    ax2.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.2f%%"))
    ax2.grid(axis="y", alpha=0.25, linewidth=0.6)
    ax2.set_xticks(DAYS)
    ax2.set_xticklabels([str(d) for d in DAYS], fontsize=8)

    plt.suptitle("Event Study — GPW 2019–2025 | Sek. energetyczno-paliwowy",
                 fontsize=9, color="grey", y=1.002)

    plt.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# ── 1. Wykresy per kategoria ───────────────────────────────────────────────────

categories = (ar_win.groupby("event_type_pl")["event_id"]
              .nunique()
              .rename("n_events")
              .reset_index()
              .query("n_events >= @MIN_N")
              .sort_values("n_events", ascending=False))

print("=" * 60)
print("GENEROWANIE WYKRESÓW AAR PER KATEGORIA")
print("=" * 60)

for _, row in categories.iterrows():
    cat      = row["event_type_pl"]
    n_events = int(row["n_events"])
    sub      = ar_win[ar_win["event_type_pl"] == cat]

    safe = cat.replace("/", "_").replace(" ", "_")
    out  = OUT_DIR / f"aar_{safe}.png"

    plot_aar_category(cat, sub, n_events, out)
    print(f"  [{n_events:4d} zd.]  {cat:<30}  → {out.name}")


# ── 2. Wykres zbiorczy — wszystkie kategorie ──────────────────────────────────

fig, ax = plt.subplots(figsize=(13, 6))

for _, row in categories.iterrows():
    cat      = row["event_type_pl"]
    n_events = int(row["n_events"])
    sub      = ar_win[ar_win["event_type_pl"] == cat]
    aar_df   = compute_aar(sub)
    color    = COLORS.get(cat, DEFAULT_COLOR)

    ax.plot(DAYS, aar_df["aar"],
            label=f"{cat} (n={n_events})",
            color=color, linewidth=2, marker="o", markersize=3)

ax.axhline(0, color="black", linewidth=0.8, linestyle="--", alpha=0.7)
ax.axvline(0, color="#B71C1C", linewidth=1.5, linestyle=":", label="Day 0")
ax.set_xlabel("Dzień względny (Day 0 = data zdarzenia)", fontsize=12)
ax.set_ylabel("AAR (%)", fontsize=12)
ax.set_title("AAR po kategoriach zdarzeń — okno [−10, +10]\n"
             "Event Study | GPW 2019–2025 | Sek. energetyczno-paliwowy",
             fontsize=13, fontweight="bold")
ax.legend(loc="lower right", fontsize=9, framealpha=0.9)
ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.2f%%"))
ax.grid(alpha=0.25, linewidth=0.6)
ax.set_xticks(DAYS)
ax.set_xticklabels([str(d) for d in DAYS], fontsize=8)
plt.tight_layout()

out = OUT_DIR / "aar_wszystkie_kategorie.png"
plt.savefig(out, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"\n  [zbiorczy]  → {out.name}")


# ── 3. Wykres CAAR per kategoria — jeden panel ────────────────────────────────

fig, ax = plt.subplots(figsize=(13, 6))

for _, row in categories.iterrows():
    cat      = row["event_type_pl"]
    n_events = int(row["n_events"])
    sub      = ar_win[ar_win["event_type_pl"] == cat]
    aar_df   = compute_aar(sub)
    caar     = aar_df["aar"].cumsum()
    color    = COLORS.get(cat, DEFAULT_COLOR)

    final = float(caar.iloc[-1])
    ax.plot(DAYS, caar.values,
            label=f"{cat} (n={n_events}, CAAR[+10]={final:+.2f}%)",
            color=color, linewidth=2, marker="o", markersize=3)

ax.axhline(0, color="black", linewidth=0.8, linestyle="--", alpha=0.7)
ax.axvline(0, color="#B71C1C", linewidth=1.5, linestyle=":", label="Day 0")
ax.set_xlabel("Dzień względny", fontsize=12)
ax.set_ylabel("CAAR (%)", fontsize=12)
ax.set_title("CAAR po kategoriach zdarzeń — okno [−10, +10]\n"
             "Event Study | GPW 2019–2025 | Sek. energetyczno-paliwowy",
             fontsize=13, fontweight="bold")
ax.legend(loc="lower right", fontsize=9, framealpha=0.9)
ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.2f%%"))
ax.grid(alpha=0.25, linewidth=0.6)
ax.set_xticks(DAYS)
ax.set_xticklabels([str(d) for d in DAYS], fontsize=8)
plt.tight_layout()

out = OUT_DIR / "caar_wszystkie_kategorie.png"
plt.savefig(out, dpi=150, bbox_inches="tight")
plt.close(fig)
print(f"  [CAAR zbiorczy]  → {out.name}")

print(f"\nWszystkie wykresy zapisano w:\n  {OUT_DIR}")
