from __future__ import annotations

import re
from inspect import getsource
from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
import numpy as np
from IPython.core.oinspect import pylight
from IPython.display import display, HTML, Markdown
from matplotlib.font_manager import findSystemFonts, fontManager
from matplotlib.patches import Rectangle
from scipy.spatial.distance import cdist

from analysis_helpers.constants import CONTENT_WARNING, EVENTSEG_EDGECOLOR, FONTS_DIR
from analysis_helpers.internals import _imported_from_notebook

if TYPE_CHECKING:
    from typing import Any,Callable
    from numpy.typing import ArrayLike


def draw_event_bounds(
        ax: plt.Axes,
        event_bounds: list[tuple[int, int]],
        **rect_kwargs: dict[str, Any]
) -> list[Rectangle]:
    facecolor = rect_kwargs.pop('facecolor', rect_kwargs.pop('fc', 'none'))
    patches = []
    for onset, offset in event_bounds:
        size = offset - onset + 1
        rect = Rectangle((onset - 0.5, onset - 0.5),
                         width=size,
                         height=size,
                         edgecolor=EVENTSEG_EDGECOLOR,
                         facecolor=facecolor,
                         **rect_kwargs)
        ax.add_patch(rect)
        patches.append(rect)
    return patches


def dtw(
        series_a: ArrayLike,
        series_b: ArrayLike,
        metric: str | Callable[[ArrayLike, ArrayLike], float] = 'cosine',
        norm_cost: bool = True
) -> tuple[float, list[tuple[int, int]]]:
    """
    Monotonic dynamic time warping.

    Temporally aligns two feature time series and returns the alignment
    cost along with the warp path that produced it.

    Parameters
    ----------
    series_a, series_b : array-like of shape (n_samples, n_features)
        The two feature sequences to align.
    metric : str or callable, optional
        The metric used to compute distances between feature vectors
        (default: 'cosine'). May be any named metric accepted by
        `scipy.spatial.distance.cdist` or a callable that takes two 1D
        arrays and returns a scalar.
    norm_cost : bool, optional
        If True (default), return the average cost instead of summed
        cost so that sequences of different lengths remain comparable.

    Returns
    -------
    cost : float
        The alignment cost (length-normalized by default).
    path : list of (int, int)
        The warp path as (series_a_index, series_b_index) pairs.
    """
    distmat = cdist(series_a, series_b, metric=metric)
    len_a, len_b = distmat.shape

    # build up full cost matrix
    accum_cost = np.full((len_a + 1, len_b + 1), np.inf)
    accum_cost[0, 0] = 0.0
    for i in range(1, len_a + 1):
        for j in range(1, len_b + 1):
            cheapest_prev = min(
                accum_cost[i - 1, j - 1],  # match:      advance both series
                accum_cost[i - 1, j],      # insertion:  advance A only
                accum_cost[i, j - 1],      # deletion:   advance B only
            )
            accum_cost[i, j] = distmat[i - 1, j - 1] + cheapest_prev

    # Backtrack
    row, col = len_a, len_b
    path = []
    while row > 0 and col > 0:
        path.append((row - 1, col - 1))
        cheapest_prev = min(
            accum_cost[row - 1, col - 1],
            accum_cost[row - 1, col],
            accum_cost[row, col - 1],
        )
        if accum_cost[row - 1, col - 1] == cheapest_prev:
            row -= 1
            col -= 1
        elif accum_cost[row - 1, col] == cheapest_prev:
            row -= 1
        else:
            col -= 1

    cost = accum_cost[len_a, len_b]
    if norm_cost:
        cost /= len(path)

    return cost, path[::-1]


def format_stats(
    stat: float,
    p: float,
    stat_name: str,
    df: int | None = None,
    n_decimals_stat: int = 3,
    n_decimals_p: int = 3,
    p_min: float = 0.001,
    sep: str = '\n',
    bold: bool = False
):
    """
    General function for formatting the test statistic and p-value from
    a statistical test for display in a `matplotlib.pyplot` plot.

    Parameters
    ----------
    stat, p : float
        The test statistic and associated p-value.
    stat_name : str
        The string used to describe the test statistic in the plot
        (e.g., 't', 'r', etc.).
    df : int, optional
        The degrees of freedom associated with the test statistic. If
        not None (default), this is displayed in parentheses immediately
        after the test statistic (e.g., "t(10) = ...").
    n_decimals_stat, n_decimals_p : int, optional
        The number of decimals (default: 3) to display for the test
        statistic and p-value (if greater than `p_min`), respectively.
    p_min : float, optional
        The smallest p-value (default: 0.001) to display. Lower p-values
        are displayed as "p < `p_min`".
    sep : str, optional
        The string separating the formatted test statistic and p-value
        (e.g., "\n", ", "). Default: "\n".
    bold : bool, optional
        Whether to bold the formatted text (default: False).

    Returns
    -------
    str
        The formatted output to display in the plot.
    """
    tex_it_wrapper = '\\mathbfit' if bold else '\\mathit'

    stat_name_fmt = f'{tex_it_wrapper}{{{stat_name}}}'

    stat_text_fmt = f' = {stat:.{n_decimals_stat}f}'
    if df is not None:
        stat_text_fmt = f'({df}) {stat_text_fmt}'

    p_fmt = f'{tex_it_wrapper}{{p}}'
    if p < p_min:
        p_text_fmt = f' < {p_min}'
    else:
        p_text_fmt = f' = {p:.{n_decimals_p}f}'

    if bold:
        stat_text_fmt = f'\\mathbf{{{stat_text_fmt}}}'
        p_text_fmt = f'\\mathbf{{{p_text_fmt}}}'

    return f'${stat_name_fmt}{stat_text_fmt}${sep}${p_fmt}{p_text_fmt}$'


def mean_center(*to_center, equal_weight=True):
    """
    Mean-center one or more feature matrices by their shared centroid.

    Returns a tuple of inputs with the same shape & order as passed.
    """
    if len(to_center) == 1:
        return to_center[0] - to_center[0].mean(axis=0)

    input_was_1d = [x.ndim == 1 for x in to_center]
    to_center = [np.atleast_2d(x) for x in to_center]
    if equal_weight:
        mean_centroid = np.mean([x.mean(axis=0) for x in to_center], axis=0)
        centered = [x - mean_centroid for x in to_center]
    else:
        split_inds = np.cumsum([x.shape[0] for x in to_center])[:-1]
        stacked = np.vstack(to_center)
        stacked = stacked - stacked.mean(axis=0)
        centered = np.vsplit(stacked, split_inds)

    return tuple(c[0] if was_1d else c for c, was_1d in zip(centered, input_was_1d))


def set_figure_style():
    """
    Sets some helpful `matplotlib` options for figures generated for the
    paper. This gets called automatically whenever `analysis_helpers` is
    imported, but occasionally needs to be called again manually when
    some other function has overwritten the relevant
    `matplotlib.rcParams` (e.g., inside `seaborn.axes_style` context
    managers).
    """
    # embed text in PDFs for illustrator
    plt.rcParams['pdf.fonttype'] = 42

    # use Myriad Pro font, if available
    if FONTS_DIR.is_dir() and next(FONTS_DIR.iterdir(), None) is not None:
        # check whether the font has already been loaded by
        # `matplotlib`'s font manager
        # TODO: this is imperfect and only loads all Myriad Pro styles
        #  from FONTS_DIR if *no* Myriad Pro font is already loaded
        myriad_pro_fonts = [
            f for f in fontManager.ttflist if f.name == 'Myriad Pro'
        ]
        if len(myriad_pro_fonts) == 0:
            for font_file in findSystemFonts(fontpaths=[FONTS_DIR]):
                fontManager.addfont(font_file)

        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['font.sans-serif'] = (
                ['Myriad Pro'] + plt.rcParams['font.sans-serif']
        )


def show_content_warning() -> None:
    if _imported_from_notebook():
        display(Markdown(CONTENT_WARNING))
    else:
        plaintext_warning = re.sub(
                r"\[\*?(.+?)\*?]\(.+\)", r"\1", CONTENT_WARNING
        ).replace('&mdash;', '—')
        print(plaintext_warning)


def show_source(obj):
    try:
        src = getsource(obj)
    except TypeError:
        src = obj
    try:
        return HTML(pylight(src))
    except AttributeError:
        return src

def split_sentences(text: str) -> list[str]:
    """
    Split recall transcript into sentences, excluding sentence breaks
    inside multi-sentence quoted speech.
    """
    sentence_pattern = r"""
        (?:                                              # non-sentence-ending:
              Mr\.(?=\s)                                 #   "Mr." when followed by whitespace
            | \.(?=[A-Za-z0-9])                          #   period directly followed by a letter/digit
            | \.(?<=[A-Za-z]\.[A-Za-z]\.)(?=\s*\S)       #   final period of an abbreviation (i.e., a.k.a., etc.)
            | "[^"]*"(?<![.!?]")(?<![.!?]'")             #   quote whose contents don't end in sentence punct
            | "[^"]*[.!?]'?"(?![^A-Za-z]*(?:[A-Z]|$))    #   sentence-punct quote, but next letter is lowercase
            | [^."!?]                                    #   any other non-special character
        )*
        (?:                                              # sentence-ending:
              \.(?![A-Za-z0-9])                          #   period not followed by letter/digit
            | [!?]                                       #   exclamation or question
            | "[^"]*[.!?]'?"(?=[^A-Za-z]*(?:[A-Z]|$))    #   sentence-punct quote followed by uppercase or end-of-text
        )
    """
    return [s.strip() for s in re.findall(sentence_pattern, text, re.VERBOSE)]

