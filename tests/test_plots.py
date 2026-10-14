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
