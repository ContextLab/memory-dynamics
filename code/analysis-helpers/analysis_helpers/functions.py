from __future__ import annotations

import re
from collections import Counter
from inspect import getsource
from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
import numpy as np
from IPython.core.oinspect import pylight
from IPython.display import display, HTML, Markdown
from matplotlib.font_manager import findSystemFonts, fontManager
from matplotlib.patches import Rectangle
from scipy.spatial.distance import cdist
from scipy.stats import binomtest, chi2, norm, rankdata

from analysis_helpers.constants import CONTENT_WARNING, EVENTSEG_EDGECOLOR, FONTS_DIR
from analysis_helpers.internals import _imported_from_notebook

if TYPE_CHECKING:
    from typing import Any,Callable
    from numpy.typing import ArrayLike


def auc(
        positive: ArrayLike,
        negative: ArrayLike,
        smaller_is_positive: bool = False
) -> float:
    """
    Area under the ROC curve, computed directly from the two score
    distributions rather than by integrating a curve.

    Equals the probability that a randomly chosen positive case is ranked ahead
    of a randomly chosen negative one, with ties counting as half. Chance is
    0.5, and the measure is unaffected by how imbalanced the two groups are,
    which matters when each participant contributes a different number of each.

    Parameters
    ----------
    positive, negative : array-like
        Scores for the two groups of cases.
    smaller_is_positive : bool, optional
        True when a lower score is the evidence for a positive case, False
        (default) when a higher one is.

    Returns
    -------
    float
        The area under the curve.
    """
    positive = np.asarray(positive, dtype=float)[:, np.newaxis]
    negative = np.asarray(negative, dtype=float)[np.newaxis, :]
    ahead = (positive < negative) if smaller_is_positive else (positive > negative)
    return (ahead.sum() + 0.5 * (positive == negative).sum()) / ahead.size


def best_rdp_alignment(
        trajectory: ArrayLike,
        target: ArrayLike,
        epsilons: ArrayLike,
        metric: str | Callable[[ArrayLike, ArrayLike], float] = 'cosine'
) -> tuple[float, np.ndarray, float]:
    """
    The Ramer-Douglas-Peucker simplification of `trajectory` that best aligns
    to `target`.

    Simplifies `trajectory` at each tolerance in turn and keeps the
    simplification whose DTW alignment cost against `target` is lowest.

    Note that `target` is used to choose among the simplifications, so any test
    that then compares the chosen simplification against `target` is not
    independent of it. `rdp_sweep` returns the candidates themselves, which is
    what a matched null for that choice needs.

    Parameters
    ----------
    trajectory : array-like of shape (n_points, n_features)
        The trajectory to simplify.
    target : array-like of shape (n_target_points, n_features)
        The trajectory to align the simplifications to.
    epsilons : array-like of shape (n_tolerances,)
        The RDP tolerances to try, in increasing order.
    metric : str or callable, optional
        The distance metric used for both the simplification and the alignment
        (default: 'cosine').

    Returns
    -------
    epsilon : float
        The tolerance that produced the best-aligning simplification.
    kept : numpy.ndarray of shape (n_kept,)
        Indices into `trajectory` of the points that simplification retained.
    cost : float
        The DTW alignment cost at that tolerance.
    """
    candidates = rdp_sweep(trajectory, epsilons, metric=metric)
    costs = [
        dtw(simplified, target, metric=metric, norm_cost=True)[0]
        for _, simplified, _ in candidates
    ]
    best = int(np.argmin(costs))
    return candidates[best][0], candidates[best][2], costs[best]


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
    x : array-like of shape (n_samples,) or (n_samples, n_variables)
        The sample to resample from (e.g., one value per participant). A 2D
        array is resampled by rows, which is what an interval on a correlation
        needs: both members of a pair are kept together in every resample.
    statistic : callable, optional
        Function mapping one resample to a scalar (default: `numpy.median`).
        Receives a 1D array when `x` is 1D, and an (n_samples, n_variables)
        array when `x` is 2D.
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
    if x.ndim == 1:
        resamples = rng.choice(x, size=(n_boot, len(x)), replace=True)
        boot_stats = np.apply_along_axis(statistic, 1, resamples)
    else:
        rows = rng.integers(0, len(x), size=(n_boot, len(x)))
        boot_stats = np.array([statistic(x[r]) for r in rows])
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


def event_prominence(
        trajectory: ArrayLike,
        event_matches: ArrayLike,
        epsilons: ArrayLike,
        metric: str | Callable[[ArrayLike, ArrayLike], float] = 'cosine'
) -> dict[int, float]:
    """
    How structurally prominent each described episode event is within a recall
    trajectory.

    An event's prominence is the tolerance at which simplification first removes
    it: removed early (low tolerance) means it falls close to the line between
    its neighbors and is geometrically disposable, while surviving to a high
    tolerance means its removal would change the path's shape. Because the
    measure is read off the whole sweep, no tolerance is ever selected, and
    nothing outside `trajectory` is involved.

    Recall trajectories may return to the same episode event more than once. An
    event described several times takes the prominence of its *first-removed*
    occurrence, so an event counts as disposable when any one of its
    descriptions is. The first and last recall events are excluded, since
    simplification never removes the endpoints of a trajectory.

    Parameters
    ----------
    trajectory : array-like of shape (n_recall_events, n_features)
        A participant's recall event sequence.
    event_matches : array-like of shape (n_recall_events,)
        The episode event each recall event describes.
    epsilons : array-like of shape (n_tolerances,)
        The RDP tolerances to sweep, in increasing order.
    metric : str or callable, optional
        The distance metric used for the simplification (default: 'cosine').

    Returns
    -------
    dict
        Prominence for each episode event described by an interior recall event.
    """
    thresholds = removal_thresholds(trajectory, epsilons, metric=metric)
    # an interior point that no tolerance in the sweep removes is maximally
    # prominent, so it takes the largest tolerance tried
    thresholds = np.where(np.isnan(thresholds), np.max(epsilons), thresholds)

    event_matches = np.asarray(event_matches)
    prominence = {}
    for recall_event in range(1, len(event_matches) - 1):
        episode_event = int(event_matches[recall_event])
        prominence[episode_event] = min(
            prominence.get(episode_event, np.inf), thresholds[recall_event]
        )
    return prominence


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


def forgotten_events(
        imm_event_matches: ArrayLike,
        del_event_matches: ArrayLike
) -> tuple[set[int], set[int]]:
    """
    Which episode events a participant described immediately and then dropped.

    Prominence is defined only for events described by an *interior* recall
    event, since simplification never removes a trajectory's endpoints, so the
    pool is the set of episode events an interior immediate recall event
    describes. The delayed counts are offset by the same exclusion: one delayed
    occurrence is discounted per endpoint occurrence of that episode event, so
    that the two sessions are compared on equal footing. Without that offset an
    event described at an endpoint immediately, and once again after the delay,
    would look retained on the delayed side while being invisible on the
    immediate side.

    An event counts as forgotten when it was described more times among the
    interior immediate recall events than among the offset delayed ones, which
    captures a participant returning to an event less often as well as dropping
    it altogether.

    Parameters
    ----------
    imm_event_matches, del_event_matches : array-like
        The episode event each recall event describes, in each session.

    Returns
    -------
    pool : set of int
        Episode events described by an interior immediate recall event.
    forgotten : set of int
        Those of them the participant went on to describe less often.
    """
    imm_event_matches = np.asarray(imm_event_matches)
    del_event_matches = np.asarray(del_event_matches)

    interior_counts = Counter(imm_event_matches[1:-1].tolist())
    delayed_counts = Counter(del_event_matches.tolist())
    endpoint_counts = Counter(
        [int(imm_event_matches[0]), int(imm_event_matches[-1])]
    )

    pool = set(interior_counts)
    forgotten = {
        event for event, count in interior_counts.items()
        if count > max(0, delayed_counts.get(event, 0) - endpoint_counts.get(event, 0))
    }
    return pool, forgotten


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


def hypergeom_mc_test(
        n_good: ArrayLike,
        n_bad: ArrayLike,
        n_draws: ArrayLike,
        n_hits: ArrayLike,
        n_perms: int = 10_000,
        seed: int = 0
) -> tuple[int, float, float, np.ndarray]:
    """
    Monte Carlo test of a summed hit count against a hypergeometric null.

    Each participant contributes an independent draw without replacement, with
    their own pool size and number of draws, so the null distribution of the
    total is built by simulation rather than solved analytically. Participants
    who made no draws contribute zero to both the observed total and every
    null total, and so are inert.

    Parameters
    ----------
    n_good : array-like of shape (n_participants,)
        Number of "success" items in each participant's pool.
    n_bad : array-like of shape (n_participants,)
        Number of remaining items in each participant's pool.
    n_draws : array-like of shape (n_participants,)
        Number of items drawn from each participant's pool.
    n_hits : array-like of shape (n_participants,)
        Number of successes each participant actually drew.
    n_perms : int, optional
        Number of null totals to simulate (default: 10,000).
    seed : int, optional
        Seed for the random number generator, so the test is reproducible.

    Returns
    -------
    observed : int
        The observed total number of successes.
    expected : float
        The mean of the null distribution of that total.
    p : float
        One-sided p-value: the proportion of null totals at least as large as
        the observed total, with the observation itself added to both counts.
    null_totals : numpy.ndarray of shape (n_perms,)
        The simulated null distribution, for plotting.
    """
    rng = np.random.default_rng(seed)
    draws = rng.hypergeometric(
        n_good, n_bad, n_draws, size=(n_perms, len(np.asarray(n_good)))
    )
    null_totals = draws.sum(axis=1)
    observed = int(np.sum(n_hits))
    p = ((null_totals >= observed).sum() + 1) / (n_perms + 1)
    return observed, null_totals.mean().item(), p.item(), null_totals


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


def identification_test(
        own: ArrayLike,
        others: ArrayLike,
        smaller_is_closer: bool = True
) -> tuple[float, int, float, float, tuple[float, float]]:
    """
    Rank-1 identification accuracy and its test against chance.

    Ties are the reason this needs care. `identification_accuracy` breaks them
    fractionally, so its rank-1 value is the *expected* proportion of
    participants whose own comparison comes out on top once tied comparisons
    are ordered at random. That expectation is generally not a whole number of
    participants, and it can be much larger than the number who are the
    unique top match, so both are returned.

    Under the null that a participant's own comparison is exchangeable with the
    others, its rank is uniform over every candidate available to them --- their
    own plus the `n - 1` others, so `n` in total. Chance is therefore 1/n, not
    1/(n - 1). The p-value is the right tail of Binomial(n, 1/n) at the expected
    count, which for a fractional count means rounding it up: the null count is
    whole-numbered, so P(K >= 2.77) and P(K >= 3) are the same quantity.

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
    accuracy : float
        Tie-aware rank-1 accuracy.
    n_unique : int
        Number of participants whose own comparison is the unique top match,
        with nothing tied alongside it.
    chance : float
        The accuracy expected by chance, 1/n.
    p : float
        One-sided binomial p-value against that chance level.
    ci : tuple of float
        Wilson score interval on the proportion of unique top matches. Wilson
        rather than Wald, since the proportion sits near 0 when identification
        fails and Wald intervals misbehave there.
    """
    own = np.asarray(own, dtype=float)[:, np.newaxis]
    others = np.asarray(others, dtype=float)
    n = len(own)

    beaten = (others < own) if smaller_is_closer else (others > own)
    ties = (others == own).sum(axis=1)
    n_unique = int(((beaten.sum(axis=1) == 0) & (ties == 0)).sum())

    accuracy = identification_accuracy(
        own.ravel(), others, smaller_is_closer=smaller_is_closer
    )[0].item()
    chance = 1 / n
    p = binomtest(
        int(np.ceil(accuracy * n)), n, chance, alternative='greater'
    ).pvalue

    z = norm.ppf(0.975)
    prop = n_unique / n
    scale = 1 / (1 + z ** 2 / n)
    center = scale * (prop + z ** 2 / (2 * n))
    halfwidth = scale * z * np.sqrt(prop * (1 - prop) / n + z ** 2 / (4 * n ** 2))
    return accuracy, n_unique, chance, p, (center - halfwidth, center + halfwidth)


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


def rdp(
        trajectory: ArrayLike,
        epsilon: float,
        metric: str | Callable[[ArrayLike, ArrayLike], float] = 'euclidean',
        return_indices: bool = False
) -> np.ndarray | tuple[np.ndarray, np.ndarray]:
    """
    Simplify an n-dimensional trajectory using the Ramer-Douglas-Peucker
    algorithm.

    Parameters
    ----------
    trajectory : numpy.ndarray
        A (timepoints x features) matrix representing the curve to simplify.
    epsilon : float
        Maximum allowed distance from a point to the simplified curve. Points
        farther than epsilon from the line segment connecting their neighbors
        are retained.
    metric : str or callable
        Distance metric used when computing point-to-segment distances.
        Accepts any distance name supported by scipy.spatial.distance.cdist
        (e.g. 'euclidean', 'cosine', 'correlation') or a callable with
        signature f(u, v) -> float.
    return_indices : bool, default False
        If True, return a tuple (simplified_trajectory, indices) where
        indices is a 1D array of the retained point indices into the original
        trajectory. If False, return only the simplified trajectory.

    Returns
    -------
    numpy.ndarray or tuple
        The simplified trajectory, or (simplified_trajectory, indices) when
        return_indices is True.
    """
    def _dist(points, start, end):
        """
        Compute the distance from each point in `points` to the line segment
        defined by `start` and `end`.

        The perpendicular foot is clamped to the segment so that points past
        either endpoint are measured to the nearest endpoint instead.
        """
        segment = end - start
        seg_len_sq = np.dot(segment, segment)

        if seg_len_sq == 0:
            # Degenerate segment: start == end; distance is point-to-point.
            if callable(metric):
                return np.array([metric(p, start) for p in points])
            return cdist(points, start[np.newaxis], metric=metric).ravel()

        # Scalar projection of each point onto the segment, clamped to [0, 1].
        t = np.clip(
            np.dot(points - start, segment) / seg_len_sq,
            0.0, 1.0
        )                                           # shape (n,)
        projections = start + t[:, np.newaxis] * segment   # shape (n, d)

        if callable(metric):
            return np.array([metric(p, proj) for p, proj in zip(points, projections)])
        # cdist expects 2-D arrays.
        return cdist(points, projections, metric=metric).diagonal()

    def _rdp_indices(indices):
        """
        Recursively collect the indices of points to keep.
        Works on a view into the global `trajectory` array.
        """
        if len(indices) <= 2:
            return list(indices)

        start = trajectory[indices[0]]
        end   = trajectory[indices[-1]]
        inner = indices[1:-1]

        dists = _dist(trajectory[inner], start, end)
        max_idx = np.argmax(dists)
        max_dist = dists[max_idx]

        if max_dist > epsilon:
            pivot = max_idx + 1   # position within `indices`
            left  = _rdp_indices(indices[:pivot + 1])
            right = _rdp_indices(indices[pivot:])
            # Merge, avoiding the duplicate at the pivot.
            return left[:-1] + right
        else:
            return [indices[0], indices[-1]]

    trajectory = np.asarray(trajectory)
    kept = _rdp_indices(list(range(len(trajectory))))
    kept = np.array(kept)

    simplified = trajectory[kept]
    return (simplified, kept) if return_indices else simplified


def rdp_sweep(
        trajectory: ArrayLike,
        epsilons: ArrayLike,
        metric: str | Callable[[ArrayLike, ArrayLike], float] = 'cosine'
) -> list[tuple[float, np.ndarray, np.ndarray]]:
    """
    The distinct simplifications of `trajectory` produced by a tolerance sweep.

    Successive tolerances that leave the same number of points leave the same
    points, so each distinct simplification is returned once, at the smallest
    tolerance that produces it. The simplifications are nested: raising the
    tolerance only ever removes further points.

    Which points a given simplification retains is a property of the
    trajectory's own shape. Choosing among these candidates is therefore the
    only step at which anything outside the trajectory can enter, which is what
    makes the candidates the right thing to hold fixed when building a null for
    that choice.

    Parameters
    ----------
    trajectory : array-like of shape (n_points, n_features)
        The trajectory to simplify.
    epsilons : array-like of shape (n_tolerances,)
        The RDP tolerances to try, in increasing order.
    metric : str or callable, optional
        The distance metric used for the simplification (default: 'cosine').

    Returns
    -------
    list of (float, numpy.ndarray, numpy.ndarray)
        One (epsilon, simplified_trajectory, kept_indices) triple per distinct
        simplification, in increasing order of tolerance.
    """
    candidates = []
    n_kept_prev = None
    for epsilon in epsilons:
        simplified, kept = rdp(
            trajectory, epsilon=epsilon, metric=metric, return_indices=True
        )
        if len(kept) != n_kept_prev:
            n_kept_prev = len(kept)
            candidates.append((epsilon, simplified, kept))
        # only the endpoints are left; no further tolerance can change that
        if len(kept) == 2:
            break
    return candidates


def removal_thresholds(
        trajectory: ArrayLike,
        epsilons: ArrayLike,
        metric: str | Callable[[ArrayLike, ArrayLike], float] = 'cosine'
) -> np.ndarray:
    """
    The tolerance at which simplification first removes each point.

    This grades how expendable each point is: one that survives a large
    tolerance is a point whose removal would substantially change the path's
    shape, while one removed at a small tolerance falls close to the line
    between its neighbors. Nothing outside `trajectory` is involved.

    The first and last points are never removed, so they come back as NaN.

    Parameters
    ----------
    trajectory : array-like of shape (n_points, n_features)
        The trajectory to simplify.
    epsilons : array-like of shape (n_tolerances,)
        The RDP tolerances to try, in increasing order.
    metric : str or callable, optional
        The distance metric used for the simplification (default: 'cosine').

    Returns
    -------
    numpy.ndarray of shape (n_points,)
        The tolerance at which each point is first removed, NaN where it never
        is.
    """
    trajectory = np.asarray(trajectory)
    thresholds = np.full(len(trajectory), np.nan)
    for epsilon, _, kept in rdp_sweep(trajectory, epsilons, metric=metric):
        removed = np.setdiff1d(np.arange(len(trajectory)), kept)
        thresholds[removed[np.isnan(thresholds[removed])]] = epsilon
    return thresholds


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

