import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import FuncFormatter, MaxNLocator
import numpy as np
import pandas as pd


WORK = Path(__file__).parent
OUT = Path("data/processed/thesis_outputs")
sample = pd.read_csv(WORK / "proba_m3.csv")
model = json.loads((WORK / "model_m3a.json").read_text(encoding="utf-8-sig"))
if "terms" in model:
    terms = model["terms"]
    model = {
        "no": {"intercept": terms["const"]["coef"], "slope": terms["tone_no"]["coef"]},
        "yes": {"intercept": terms["const"]["coef"] + terms["adverse"]["coef"], "slope": terms["tone_yes"]["coef"]},
    }
assert sample["event_id"].is_unique and sample["car"].notna().all()
assert set(sample["adverse_revision"]) == {"yes", "no"}
assert set(sample["source"]) == {"exact", "broad"}
sample["CAR"] = sample["car"] * 100
tones = sample["tone_per_100_words"]
min_x, max_x = tones.min(), tones.max()
span_x = max_x - min_x
colors = {"yes": "#9C3B2D", "no": "#2D5C83"}

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 11, "figure.facecolor": "white",
    "axes.facecolor": "white", "axes.labelcolor": "#223042", "text.color": "#223042",
    "xtick.color": "#455567", "ytick.color": "#455567", "axes.edgecolor": "#C5CED7",
})
fig, ax = plt.subplots(figsize=(10.8, 7.3))
fig.subplots_adjust(left=0.11, bottom=0.15, right=0.96, top=0.76)
fig.text(0.11, 0.934, "Ton wcześniejszej narracji a reakcja rynku", size=20, weight="bold")
counts = sample["source"].value_counts()
fig.text(0.11, 0.881, f"Model M3  ·  {len(sample)} zdarzeń  ·  "
         f"{counts['exact']} dopasowań projektowych i {counts['broad']} ogólnych dopasowań CAPEX",
         size=10, color="#506276")
fig.text(0.11, 0.054, "Linie pokazują dopasowanie oszczędnej specyfikacji M3 w obserwowanym zakresie tonu danej grupy.",
         size=9, color="#506276")

for key, group in sample.groupby("adverse_revision"):
    for source, subset in group.groupby("source"):
        broad = source == "broad"
        ax.scatter(subset["tone_per_100_words"], subset["CAR"], s=58 if broad else 47,
                   marker="^" if broad else "o", facecolors="white" if broad else colors[key],
                   edgecolors=colors[key], linewidths=1.3 if broad else 0.7, zorder=5)
    line = model[key]
    if line["slope"] is not None:
        x = np.linspace(group["tone_per_100_words"].min(), group["tone_per_100_words"].max(), 100)
        y = 100 * (line["intercept"] + x * line["slope"])
        ax.plot(x, y, color=colors[key], linewidth=1.55, alpha=0.85, linestyle="--", zorder=3)

ax.set_xlim(min_x - 0.17 * span_x, max_x + 0.21 * span_x)
low, high = sample["CAR"].min() - 1.25, sample["CAR"].max() + 1.25
ax.set_ylim(low, high)
ax.set_xlabel("Ton wcześniejszego raportu (dopasowania netto na 100 słów)", labelpad=10)
ax.set_ylabel("CAR [−1,+1] (%)", labelpad=10)
ax.axhline(0, color="#768597", linewidth=0.9, zorder=2)
ax.axvline(0, color="#BEC8D3", linewidth=0.85, zorder=2)
ax.grid(axis="y", color="#E5EAF0", linewidth=0.85)
ax.yaxis.set_major_locator(MaxNLocator(7, integer=True))
ax.xaxis.set_major_locator(MaxNLocator(8))
ax.xaxis.set_major_formatter(FuncFormatter(lambda val, _: f"{val:g}".replace("-", "−").replace(".", ",")))
ax.spines[["right", "top"]].set_visible(False)
ax.tick_params(length=0, pad=7)

# Allocate two vertical lanes outside the central cluster so event labels stay legible.
near_zero = sample.loc[sample["adverse_revision"].eq("yes")].copy()
near_zero["label_side"] = np.where(near_zero["tone_per_100_words"].lt(-0.22 * span_x), "lewy", "prawy")
for side, group in near_zero.sort_values("CAR").groupby("label_side"):
    right = side == "prawy"
    y_positions = group["CAR"].to_numpy(copy=True)
    gap = 0.59
    for i in range(1, len(y_positions)):
        y_positions[i] = max(y_positions[i], y_positions[i - 1] + gap)
    if y_positions[-1] > high - 0.35:
        y_positions -= y_positions[-1] - (high - 0.35)
    positions = group["tone_per_100_words"]
    label_x = (max(0, positions.max()) + span_x * 0.075) if right else (positions.min() - span_x * 0.045)
    for record, label_y in zip(group.itertuples(index=False), y_positions):
        ax.annotate(record.event_id, xy=(record.tone_per_100_words, record.CAR), xytext=(label_x, label_y),
                    fontsize=8.1, color="#6E3028", ha="left" if right else "right", va="center",
                    bbox=dict(facecolor="white", edgecolor="none", alpha=0.94, pad=1.1),
                    arrowprops=dict(arrowstyle="-", color="#A9827D", linewidth=0.55, shrinkA=2, shrinkB=4),
                    zorder=7, annotation_clip=False)

legend = [
    Line2D([], [], marker="o", color=colors["yes"], linestyle="none", label="Niekorzystne korekty"),
    Line2D([], [], marker="o", color=colors["no"], linestyle="none", label="Pozostałe zdarzenia"),
    Line2D([], [], marker="^", color="#506276", markerfacecolor="white", linestyle="none", label="Ogólna narracja CAPEX"),
]
fig.legend(handles=legend, loc="upper left", bbox_to_anchor=(0.103, 0.835), ncols=3, frameon=False, fontsize=9.5)
fig.savefig(OUT / "wykres_1_ton_vs_car.png", dpi=300, facecolor="white")
fig.savefig(WORK / "plot1_preview.png", dpi=105, facecolor="white")
plt.close(fig)
