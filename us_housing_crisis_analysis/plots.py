"""Shared matplotlib style for paper figures."""

from pathlib import Path

from cycler import cycler
import matplotlib.pyplot as plt

from us_housing_crisis_analysis.config import FIGURES_DIR

# Categorical series colors, assigned in this fixed order (never cycled past the end). The first
# two were checked for colorblind separation and contrast on the white surface.
SERIES_COLORS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
# A second cue besides color, so series stay distinct in grayscale and for colorblind readers
SERIES_MARKERS = ["o", "s", "^", "D", "v", "P", "X", "*"]
TEXT = "#1f1f1e"
MUTED = "#6b6a64"


def apply_style() -> None:
    plt.rcParams.update(
        {
            "figure.figsize": (8, 4.5), "figure.dpi": 100, "figure.facecolor": "white",
            "axes.spines.top": False, "axes.spines.right": False, "axes.edgecolor": MUTED,
            "axes.grid": True, "axes.axisbelow": True, "grid.alpha": 0.3, "grid.linewidth": 0.6,
            "axes.prop_cycle": cycler(color=SERIES_COLORS),
            "lines.linewidth": 2, "lines.markersize": 6,
            "font.size": 11, "text.color": TEXT, "axes.labelcolor": TEXT,
            "xtick.color": MUTED, "ytick.color": MUTED, "legend.frameon": False,
        }
    )


def save_figure(fig, name: str) -> Path:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    path = FIGURES_DIR / f"{name}.png"
    fig.savefig(path, dpi=200, bbox_inches="tight")
    return path


def spread_labels(y, min_gap: float) -> list[float]:
    """Label positions for line ends at heights y: same order, at least min_gap apart, each crowded
    group spread evenly about the mean of its members; labels clear of the others stay put."""
    order = sorted(range(len(y)), key=lambda i: y[i])
    groups = []  # [members in order, center]
    for i in order:
        groups.append([[i], float(y[i])])
        while len(groups) > 1:
            (a, ca), (b, cb) = groups[-2], groups[-1]
            if (cb - (len(b) - 1) * min_gap / 2) - (ca + (len(a) - 1) * min_gap / 2) >= min_gap:
                break
            members = a + b
            groups[-2:] = [[members, sum(float(y[j]) for j in members) / len(members)]]
    out = [0.0] * len(y)
    for members, center in groups:
        for k, j in enumerate(members):
            out[j] = center + (k - (len(members) - 1) / 2) * min_gap
    return out
