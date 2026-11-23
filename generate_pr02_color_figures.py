"""Create color PR02 figures from the verified dataset and experiment outputs."""
from pathlib import Path
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "figures/pr02"
OUT.mkdir(parents=True, exist_ok=True)
train = pd.read_csv(ROOT / "data/train.csv")
test = pd.read_csv(ROOT / "data/test.csv")

plt.rcParams.update({
    "font.family": "serif", "font.size": 9,
    "axes.edgecolor": "#333333", "axes.labelcolor": "#222222",
    "text.color": "#222222", "xtick.color": "#222222",
    "ytick.color": "#222222", "axes.titlecolor": "#222222",
    "figure.facecolor": "white", "axes.facecolor": "white",
    "savefig.facecolor": "white",
})
TRAIN_COLOR = "#2878B5"
TEST_COLOR = "#F28E2B"
ATTACK_COLOR = "#D64F4F"
NORMAL_COLOR = "#4C9F70"
MODEL_COLORS = ["#2878B5", "#E28E2C", "#5A9F68"]

# Partition label and category composition.
cats = ["Normal", "Generic", "Exploits", "Fuzzers", "DoS", "Reconnaissance",
        "Analysis", "Backdoor", "Shellcode", "Worms"]
fig, axs = plt.subplots(1, 2, figsize=(11, 4.2))
for ax, cols, title in [(axs[0], ["Normal", "Attack"], "Binary label"),
                        (axs[1], cats, "Attack category")]:
    x = np.arange(len(cols)); width = .38
    for j, (data, label, color) in enumerate([(train, "Train", TRAIN_COLOR), (test, "Test", TEST_COLOR)]):
        vals = [(data.attack_cat.eq(c).mean() * 100 if c != "Attack"
                 else data.label.eq(1).mean() * 100) for c in cols]
        ax.bar(x + (j - .5) * width, vals, width, label=label, color=color,
               edgecolor="white", linewidth=.7)
    ax.set_xticks(x, ["Attack" if c == "Attack" else c for c in cols],
                  rotation=30 if len(cols) > 2 else 0,
                  ha="right" if len(cols) > 2 else "center")
    ax.set_ylabel("Percent of partition")
    ax.set_title(title)
    ax.grid(axis="y", color="#D9DEE5", linewidth=.5)
    ax.set_axisbelow(True)
    ax.legend(frameon=False)
fig.tight_layout()
fig.savefig(OUT / "class_distribution_color.png", dpi=240, bbox_inches="tight")
plt.close(fig)

# Selected numeric feature distributions (log1p is for display only).
selected = ["dur", "sbytes", "dbytes", "rate", "sttl", "dttl", "sload", "smean", "ct_srv_src", "ct_state_ttl"]
fig, axs = plt.subplots(2, 5, figsize=(12, 5.2))
for ax, col in zip(axs.flat, selected):
    for data, partition, linestyle, alpha in [(train, "Train", "-", .42), (test, "Test", "--", 1)]:
        for is_attack, label, color in [(False, "Normal", NORMAL_COLOR), (True, "Attack", ATTACK_COLOR)]:
            values = np.log1p(np.clip(data.loc[data.label.eq(int(is_attack)), col].to_numpy(dtype=float), 0, None))
            ax.hist(values, bins=35, density=True, color=color, alpha=alpha,
                    histtype="stepfilled" if partition == "Train" else "step",
                    edgecolor=color, linewidth=.65,
                    linestyle=linestyle)
    ax.set_title(f"log1p({col})", fontsize=8)
    ax.tick_params(labelsize=7)
    ax.grid(axis="y", color="#E4E7EB", linewidth=.4)
fig.legend(handles=[
    Patch(facecolor=NORMAL_COLOR, edgecolor=NORMAL_COLOR, alpha=.55, label="Train normal"),
    Patch(facecolor=ATTACK_COLOR, edgecolor=ATTACK_COLOR, alpha=.55, label="Train attack"),
    Line2D([0], [0], color=NORMAL_COLOR, linestyle="--", label="Test normal"),
    Line2D([0], [0], color=ATTACK_COLOR, linestyle="--", label="Test attack"),
], loc="upper center", ncol=4, frameon=False, fontsize=8)
fig.tight_layout(rect=(0, 0, 1, .93))
fig.savefig(OUT / "selected_feature_distributions_color.png", dpi=240, bbox_inches="tight")
plt.close(fig)

# E1 false-positive rate comparison.
e1 = pd.read_csv(ROOT / "results/pr02/E1_overall.csv")
fig, ax = plt.subplots(figsize=(7, 4.4)); x = np.arange(len(e1))
bars = ax.bar(x, e1.fpr, color=MODEL_COLORS, edgecolor="white", linewidth=.8)
for bar, value in zip(bars, e1.fpr):
    ax.text(bar.get_x() + bar.get_width() / 2, value + .012, f"{value:.3f}", ha="center", fontsize=8)
ax.set_xticks(x, e1.model, rotation=10)
ax.set_ylim(0, max(.4, float(e1.fpr.max() + .08)))
ax.set_ylabel("False positive rate on normal test traffic")
ax.set_title("E1 reference false positive rate at threshold 0.5")
ax.grid(axis="y", color="#D9DEE5", linewidth=.5); ax.set_axisbelow(True)
fig.tight_layout()
fig.savefig(OUT / "e1_false_positive_rate_color.png", dpi=240, bbox_inches="tight")
plt.close(fig)

# E2 category recall with 95% Wilson intervals.
e2 = pd.read_csv(ROOT / "results/pr02/E2_loaco.csv")
models = e1.model.tolist(); categories = e2.held_out_category.drop_duplicates().tolist()
x = np.arange(len(categories)); width = .25
fig, ax = plt.subplots(figsize=(11, 4.8))
for j, (model, color) in enumerate(zip(models, MODEL_COLORS)):
    data = e2[e2.model.eq(model)].set_index("held_out_category").loc[categories]
    ax.bar(x + (j - 1) * width, data.attack_recall, width, label=model,
           color=color, edgecolor="white", linewidth=.6,
           yerr=[data.attack_recall - data.recall_ci_low, data.recall_ci_high - data.attack_recall],
           capsize=2, error_kw={"elinewidth": .7, "ecolor": "#333333"})
ax.set_xticks(x, categories, rotation=25, ha="right")
ax.set_ylim(0, 1.08)
ax.set_ylabel("Recall on held-out attack category")
ax.set_title("LOACO attack recall at threshold 0.5 with 95% Wilson intervals")
ax.legend(frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(.5, 1.16))
ax.grid(axis="y", color="#D9DEE5", linewidth=.5); ax.set_axisbelow(True)
fig.tight_layout()
fig.savefig(OUT / "loaco_recall_models_color.png", dpi=240, bbox_inches="tight")
plt.close(fig)

print(f"Saved color PR02 figures in {OUT}")
