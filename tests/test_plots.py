import itertools

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from us_housing_crisis_analysis import plots


def test_save_figure_writes_png(tmp_path, monkeypatch):
    monkeypatch.setattr(plots, "FIGURES_DIR", tmp_path)
    plots.apply_style()
    fig, ax = plt.subplots()
    ax.plot([0, 1], [0, 1])
    path = plots.save_figure(fig, "smoke")
    assert path == tmp_path / "smoke.png" and path.stat().st_size > 0


def test_spread_labels_keeps_a_minimum_gap_and_order():
    y = [0.172, 0.184, 0.30, 0.10]
    out = plots.spread_labels(y, min_gap=0.02)
    order = sorted(range(len(y)), key=y.__getitem__)
    gaps = [out[b] - out[a] for a, b in itertools.pairwise(order)]
    assert min(gaps) >= 0.02 - 1e-12  # same order as the data, at least min_gap apart
    assert out[2] == 0.30 and out[3] == 0.10  # labels already clear of the others stay put
    assert abs((out[0] + out[1]) / 2 - (0.172 + 0.184) / 2) < 1e-12  # a crowded pair spreads about its middle
