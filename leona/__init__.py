"""
leona — Leonardo da Vinci colormaps for scientific figures.

Three perceptually-ordered colormaps (sequential, monotone in lightness)
distilled from the palettes of three da Vinci paintings:

    mona    — Mona Lisa            (olive / umber / gold)
    mundi   — Salvator Mundi       (ultramarine / cream)
    ermine  — Lady with an Ermine  (oxblood / blue / tan)

On import, every colormap and its ``_r`` reversed variant is registered with
matplotlib, so the names work exactly like the built-ins::

    import leona
    import matplotlib.pyplot as plt
    plt.imshow(data, cmap="mona")      # by name
    plt.imshow(data, cmap="mundi_r")   # reversed
    plt.imshow(data, cmap=leona.mona)  # or the object directly

Regenerate the showcase figure with ``leona.preview(save="leona_palettes.png")``.
"""

from __future__ import annotations

import warnings

import matplotlib as mpl
from matplotlib.colors import LinearSegmentedColormap

__version__ = "0.1.0"
__all__ = [
    "PALETTES",
    "cmaps",
    "get",
    "register",
    "list_palettes",
    "preview",
    "mona",
    "mundi",
    "ermine",
]

# ---------------------------------------------------------------------------
# Palette definitions: five hex stops each, dark -> light, evenly spaced.
# Ordering is deliberately monotone in lightness so the ramps survive
# colour-vision-deficiency simulation and grayscale conversion.
# ---------------------------------------------------------------------------
PALETTES: dict[str, list[str]] = {
    "mona":   ["#181211", "#314036", "#5F6146", "#987954", "#DDC89A"],
    "mundi":  ["#080C11", "#1F3A5F", "#A67F5D", "#D4C5B3", "#D5E6F0"],
    "ermine": ["#0D0B0A", "#4A1C16", "#2D5B7C", "#C29167", "#EBE0CE"],
}

_N = 256  # quantization of the continuous ramp


def _build(name: str, stops: list[str]) -> LinearSegmentedColormap:
    return LinearSegmentedColormap.from_list(name, stops, N=_N)


# Forward + reversed colormap objects, keyed by name.
cmaps: dict[str, LinearSegmentedColormap] = {}
for _name, _stops in PALETTES.items():
    _cm = _build(_name, _stops)
    cmaps[_name] = _cm
    cmaps[f"{_name}_r"] = _cm.reversed()  # .reversed() appends "_r" to the name


def register(force: bool = True) -> None:
    """Register every leona colormap with matplotlib's global registry.

    Called automatically on import. Safe to call repeatedly; ``force=True``
    lets it overwrite an existing registration of the same name.
    """
    with warnings.catch_warnings():
        # force=True deliberately overwrites our own names on re-import/re-call;
        # matplotlib's "Overwriting the cmap" notice is just noise in that case.
        warnings.filterwarnings("ignore", message="Overwriting the cmap",
                                category=UserWarning)
        for name, cm in cmaps.items():
            try:
                mpl.colormaps.register(cm, name=name, force=force)
            except ValueError:
                # Name already present and force=False — keep the existing one.
                pass


def get(name: str) -> LinearSegmentedColormap:
    """Return a leona colormap object by name, e.g. ``"mona"`` or ``"mona_r"``."""
    try:
        return cmaps[name]
    except KeyError:
        raise KeyError(
            f"unknown leona colormap {name!r}; "
            f"available: {', '.join(sorted(cmaps))}"
        ) from None


def list_palettes() -> list[str]:
    """Return the base palette names (without the ``_r`` reversed variants)."""
    return list(PALETTES)


# Convenience top-level handles.
mona = cmaps["mona"]
mundi = cmaps["mundi"]
ermine = cmaps["ermine"]

# Register on import so string names work immediately (viridis-style).
register()


# ---------------------------------------------------------------------------
# Optional showcase figure. Kept self-contained so the core package depends
# only on numpy + matplotlib; scipy is imported lazily here.
# ---------------------------------------------------------------------------
def _text_color_on_white(hexc: str, thresh: float = 0.6) -> str:
    """Pick a legible label colour on a white background.

    Returns the stop's own colour for dark stops, else a muted grey. The
    choice is luminance-based, so it stays correct if stops are reordered or
    palettes of other lengths are added.
    """
    h = hexc.lstrip("#")
    r, g, b = (int(h[i:i + 2], 16) / 255 for i in (0, 2, 4))
    luminance = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return hexc if luminance < thresh else "#666666"


def _tufte(ax):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_position(("outward", 10))
        ax.spines[side].set_color("#888888")
    return ax


def preview(save: str | None = None, dpi: int = 150):
    """Render the canonical 3x3 showcase (ramp, heatmap, barplot per palette).

    Returns the matplotlib ``Figure``. Requires scipy for the heatmap
    smoothing; install with ``pip install "leona[preview]"``.
    """
    import numpy as np
    import matplotlib.pyplot as plt

    try:
        from scipy.ndimage import gaussian_filter
    except ImportError as exc:  # pragma: no cover
        raise ImportError(
            "leona.preview() needs scipy for the heatmap smoothing; "
            'install it with `pip install "leona[preview]"` or `pip install scipy`.'
        ) from exc

    fig = plt.figure(figsize=(16, 10))
    fig.suptitle(
        "leona palettes: mona, mundi, ermine",
        fontsize=18, fontweight="bold", y=0.96,
    )
    gs = fig.add_gridspec(
        3, 3, width_ratios=[1, 1.2, 1.2], hspace=0.5, wspace=0.2,
    )

    rng = np.random.default_rng(42)
    heat = gaussian_filter(rng.random((40, 60)), sigma=3.0)

    bar_heights = [85, 120, 65, 150, 95]
    bar_x = np.arange(len(bar_heights))
    gradient = np.vstack([np.linspace(0, 1, 256)] * 2)

    for i, (name, stops) in enumerate(PALETTES.items()):
        cmap = cmaps[name]

        # --- continuous ramp ---
        ax_pal = fig.add_subplot(gs[i, 0])
        ax_pal.imshow(gradient, aspect="auto", cmap=cmap)
        ax_pal.set_axis_off()
        # Bold palette name on top; smaller descriptor below it, matching the
        # font size used by the heatmap and barplot titles.
        ax_pal.set_title(name, fontsize=13, loc="left", pad=24, fontweight="bold")
        ax_pal.text(
            0.0, 1.03, "Continuous Sliding Palette",
            transform=ax_pal.transAxes, ha="left", va="bottom",
            fontsize=11, color="#444444",
        )

        # --- heatmap ---
        ax_heat = fig.add_subplot(gs[i, 1])
        ax_heat.imshow(heat, cmap=cmap, origin="lower")
        ax_heat.set_axis_off()
        ax_heat.set_title(
            "Topographic Heatmap", fontsize=11, loc="left", color="#444444",
        )

        # --- categorical barplot ---
        ax_bar = fig.add_subplot(gs[i, 2])
        _tufte(ax_bar)
        ax_bar.bar(bar_x, bar_heights, color=stops, edgecolor="white", width=0.6)
        for x, v, stop in zip(bar_x, bar_heights, stops):
            ax_bar.text(
                x, v + 5, str(v), ha="center", va="bottom",
                fontsize=10, fontweight="bold", color=_text_color_on_white(stop),
            )
        ax_bar.set_xticks(bar_x)
        ax_bar.set_xticklabels([f"Cat {j + 1}" for j in bar_x], fontsize=9)
        ax_bar.tick_params(axis="x", length=0)
        ax_bar.spines["left"].set_visible(False)
        ax_bar.set_yticks([])
        ax_bar.set_ylim(0, max(bar_heights) * 1.3)
        ax_bar.set_title(
            "Categorical Barplot", fontsize=11, loc="left", color="#444444",
        )

    if save:
        fig.savefig(save, bbox_inches="tight", dpi=dpi)
    return fig


if __name__ == "__main__":
    preview(save="leona_palettes.png")
    print("wrote leona_palettes.png")
