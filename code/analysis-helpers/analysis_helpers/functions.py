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
from scipy.stats import chi2, rankdata

from analysis_helpers.constants import CONTENT_WARNING, EVENTSEG_EDGECOLOR, FONTS_DIR
from analysis_helpers.internals import _imported_from_notebook

if TYPE_CHECKING:
    from typing import Any,Callable
    from numpy.typing import ArrayLike


def bootstrap_ci(
        x: ArrayLike,
        statistic: Callable[[ArrayLike], float] = np.median,
        confidence: float = 0.95,
        n_boot: int = 10_000,
        seed: int = 0
) -> tuple[float, float]:
    """
    Percentile bootstrap confidence interval for a statistic of `x`.

    Parameters
    ----------
    x : array-like of shape (n_samples,)
        The sample to resample from (e.g., one value per participant).
    statistic : callable, optional
        Function mapping a 1D array to a scalar (default: `numpy.median`).
    confidence : float, optional
        Width of the interval (default: 0.95).
    n_boot : int, optional
        Number of bootstrap resamples (default: 10,000).
    seed : int, optional
        Seed for the random number generator, so intervals are reproducible.

    Returns
    -------
    tuple of float
        The (lower, upper) bounds of the interval.
    """
    x = np.asarray(x, dtype=float)
    rng = np.random.default_rng(seed)
    resamples = rng.choice(x, size=(n_boot, len(x)), replace=True)
    boot_stats = np.apply_along_axis(statistic, 1, resamples)
    tail = (1 - confidence) / 2 * 100
    lower, upper = np.percentile(boot_stats, [tail, 100 - tail])
    return lower.item(), upper.item()


def cochrans_q(recounted: ArrayLike) -> tuple[float, int, float]:
    """
    Cochran's Q test for a (participants x episode events) binary matrix, under
    the null hypothesis that every episode event was equally likely to be
    recounted. Q is distributed as chi-squared with (n_events - 1) degrees of
    freedom.

    Unlike a goodness-of-fit test on the per-event totals, Q conditions on the
    number of events each participant described. That matters here: a
    participant can describe a given episode event at most once, and describes
    most of them, so treating each description as an independent draw would
    badly overestimate how much the per-event totals should vary by chance.

    Returns
    -------
    tuple
        The test statistic Q, its degrees of freedom, and the p-value.
    """
    recounted = np.asarray(recounted)
    n_events = recounted.shape[1]
    event_counts = recounted.sum(axis=0)
    participant_counts = recounted.sum(axis=1)
    numerator = n_events * (n_events - 1) * ((event_counts - event_counts.mean()) ** 2).sum()
    denominator = n_events * participant_counts.sum() - (participant_counts ** 2).sum()
    q = numerator / denominator
    df = n_events - 1
    return q.item(), df, chi2.sf(q, df).item()


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


def events_recounted(event_matches: ArrayLike, n_events: int) -> np.ndarray:
    """
    Binary vector indicating which episode events a participant described in a
    given session. A participant who returned to the same episode event more
    than once within a session is counted only once.

    Parameters
    ----------
    event_matches : array-like of shape (n_recall_events,)
        The episode event each of a participant's recall events describes.
    n_events : int
        The number of events in the episode.

    Returns
    -------
    numpy.ndarray of shape (n_events,)
        1 where the episode event was described at least once, else 0.
    """
    recounted = np.zeros(n_events, dtype=int)
    recounted[np.unique(event_matches)] = 1
    return recounted


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


def identification_accuracy(
        own: ArrayLike,
        others: ArrayLike,
        smaller_is_closer: bool = True
) -> np.ndarray:
    """
    Tie-aware identification ("fingerprinting") accuracy as a function of the
    rank cutoff k.

    For each participant, asks whether the comparison against their own other
    session ranks among the k closest of all the comparisons available to them.
    Element k - 1 of the returned array is the proportion of participants for
    whom it does, so element 0 is the rank-1 (top match) accuracy and the array
    rises monotonically to 1.

    Ties are resolved fractionally rather than optimistically: a participant
    whose own comparison ties with `t` others contributes the probability that
    a random ordering of the tied group would place it within the cutoff.

    Parameters
    ----------
    own : array-like of shape (n_participants,)
        Each participant's own-session comparison value.
    others : array-like of shape (n_participants, n_participants - 1)
        The same participant's comparison values against everyone else.
    smaller_is_closer : bool, optional
        True when the values are distances or costs (default), False when they
        are similarities.

    Returns
    -------
    numpy.ndarray of shape (n_participants,)
        Accuracy at each rank cutoff k = 1 ... n_participants.
    """
    own = np.asarray(own, dtype=float)[:, np.newaxis]
    others = np.asarray(others, dtype=float)
    if smaller_is_closer:
        better = (others < own).sum(axis=1)
    else:
        better = (others > own).sum(axis=1)
    ties = (others == own).sum(axis=1)
    ks = np.arange(1, others.shape[1] + 2)
    # of the (ties + 1) tied candidates, how many fit below the cutoff
    room = np.clip(ks[:, np.newaxis] - better, 0, ties + 1)
    return (room / (ties + 1)).mean(axis=1)


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


def percentile_ranks(
        own: ArrayLike,
        others: ArrayLike,
        smaller_is_closer: bool = True
) -> np.ndarray:
    """
    Rank each participant's own-session comparison within the distribution of
    their comparisons against everyone else, as a proportion.

    A value of 1 means the own-session comparison was closer than every other
    comparison available to that participant; 0.5 is chance. Ties count as
    half, matching the convention used throughout these analyses.

    Parameters
    ----------
    own : array-like of shape (n_participants,)
        Each participant's own-session comparison value.
    others : array-like of shape (n_participants, n_participants - 1)
        The same participant's comparison values against everyone else.
    smaller_is_closer : bool, optional
        True when the values are distances or costs (default), False when they
        are similarities.

    Returns
    -------
    numpy.ndarray of shape (n_participants,)
        The percentile rank for each participant.
    """
    own = np.asarray(own, dtype=float)[:, np.newaxis]
    others = np.asarray(others, dtype=float)
    if smaller_is_closer:
        beaten = (own < others).sum(axis=1)
    else:
        beaten = (own > others).sum(axis=1)
    ties = (own == others).sum(axis=1)
    return (beaten + 0.5 * ties) / others.shape[1]


def rank_biserial(differences: ArrayLike) -> float:
    """
    Matched-pairs rank-biserial correlation, the effect size accompanying a
    Wilcoxon signed-rank test.

    Computed as the difference between the proportion of the total signed rank
    mass falling on positive and on negative differences, so it ranges from -1
    (every pair decreased) to +1 (every pair increased). Zero differences are
    dropped before ranking, as they are by the test itself.

    Parameters
    ----------
    differences : array-like of shape (n_pairs,)
        The paired differences submitted to the test.

    Returns
    -------
    float
        The rank-biserial correlation.
    """
    differences = np.asarray(differences, dtype=float)
    differences = differences[differences != 0]
    ranks = rankdata(np.abs(differences))
    total = ranks.sum()
    return ((ranks[differences > 0].sum() - ranks[differences < 0].sum()) / total).item()


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

