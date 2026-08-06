import itertools
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.spatial.distance import pdist

import embedding_config as config


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


def n_self_intersections(path, eps=1e-9):
    """
    Count the points at which a polyline crosses or touches itself.
    Shared joints between consecutive segments and shared start/endpoint
    for a closed path are ignored.

    Parameters
    ----------
    path : array-like
        (N, 2) array of segment start/endpoints
    eps : float
        minimal tolerance value for comparisons to correct for
        differences due to floating point math

    Returns
    -------
    int
        the number of self-intersections in the path
    """
    def _same_point(a, b):
        return ((np.abs(a[:, 0] - b[:, 0]) <= eps) &
                (np.abs(a[:, 1] - b[:, 1]) <= eps))

    def _cross(origin, a, b):
        return ((a[:, 0] - origin[:, 0]) * (b[:, 1] - origin[:, 1]) -
                (a[:, 1] - origin[:, 1]) * (b[:, 0] - origin[:, 0]))

    def _lies_on_segment(point, seg_start, seg_end, seg_axis):
        """
        Check if `point` falls along the path from `seg_start` to
        `seg_end` (including endpoints)
        """
        on_line = np.abs(_cross(seg_start, seg_end, point)) <= eps
        p = point[pair_ixs, seg_axis]
        lo = np.minimum(seg_start[pair_ixs, seg_axis], seg_end[pair_ixs, seg_axis])
        hi = np.maximum(seg_start[pair_ixs, seg_axis], seg_end[pair_ixs, seg_axis])
        return on_line & (p >= lo - eps) & (p <= hi + eps)


    points = np.asarray(path, dtype=float)
    num_segments = len(points) - 1
    if num_segments < 2:
        return 0

    # ignore shared start/endpoint for closed path
    path_is_closed = np.abs(points[0] - points[-1]).max() <= eps

    seg_starts = points[:-1]
    seg_ends = points[1:]
    i, j = np.triu_indices(num_segments, k=1)
    start_i, end_i = seg_starts[i], seg_ends[i]
    start_j, end_j = seg_starts[j], seg_ends[j]
    pair_ixs = np.arange(len(i))

    # orientation of each segment's endpoints relative to other
    # segments' supporting lines
    # > 0: left of line; < 0: right of line; == 0: on the line
    start_i_vs_j = _cross(start_j, end_j, start_i)
    end_i_vs_j = _cross(start_j, end_j, end_i)
    start_j_vs_i = _cross(start_i, end_i, start_j)
    end_j_vs_i = _cross(start_i, end_i, end_j)

    # fully collinear: all four endpoints lie on the shared supporting line.
    collinear = ((np.abs(start_i_vs_j) <= eps) &
                 (np.abs(end_i_vs_j) <= eps) &
                 (np.abs(start_j_vs_i) <= eps) &
                 (np.abs(end_j_vs_i) <= eps))

    # "proper" crossings: one segment's endpoints straddle other's line,
    # so they intersect at an interior point:
    is_proper_crossing = (~collinear &
                          (start_i_vs_j * end_i_vs_j < 0) &
                          (start_j_vs_i * end_j_vs_i < 0))

    # check whether point lies within a segment
    # compare coords along each segment's dominant axis to avoid
    # degenerate vertical case
    axis_i = np.where(
        np.abs(end_i[:, 0] - start_i[:, 0]) >= np.abs(end_i[:, 1] - start_i[:, 1]), 0, 1
    )
    axis_j = np.where(
        np.abs(end_j[:, 0] - start_j[:, 0]) >= np.abs(end_j[:, 1] - start_j[:, 1]), 0, 1
    )
    start_i_on_j = _lies_on_segment(start_i, start_j, end_j, axis_j)
    end_i_on_j = _lies_on_segment(end_i, start_j, end_j, axis_j)
    start_j_on_i = _lies_on_segment(start_j, start_i, end_i, axis_i)
    end_j_on_i = _lies_on_segment(end_j, start_i, end_i, axis_i)

    # length of collinear overlap between segment pairs along segment
    # i's dominant axis (> 0: collinear lines; == 0: shared point)
    i_lo = np.minimum(start_i[pair_ixs, axis_i], end_i[pair_ixs, axis_i])
    i_hi = np.maximum(start_i[pair_ixs, axis_i], end_i[pair_ixs, axis_i])
    j_lo = np.minimum(start_j[pair_ixs, axis_i], end_j[pair_ixs, axis_i])
    j_hi = np.maximum(start_j[pair_ixs, axis_i], end_j[pair_ixs, axis_i])
    len_overlap = np.minimum(i_hi, j_hi) - np.maximum(i_lo, j_lo)
    # ignore consecutive repeated vertices
    is_degenerate = (start_i == end_i).all(axis=1) | (start_j == end_j).all(axis=1)
    is_overlap = collinear & (len_overlap > eps) & ~is_degenerate

    # find intersection points of "proper" crossings
    dir_i = end_i - start_i
    dir_j = end_j - start_j
    denom = dir_i[:, 0] * dir_j[:, 1] - dir_i[:, 1] * dir_j[:, 0]
    # avoid zero-division warnings in non-proper crossing rows
    safe_denom = np.where(denom != 0, denom, 1.0)
    t = (((start_j[:, 0] - start_i[:, 0]) * dir_j[:, 1] -
          (start_j[:, 1] - start_i[:, 1]) * dir_j[:, 0])
         / safe_denom)
    crossing_point = start_i + t[:, None] * dir_i

    # non-crossing touches
    candidate_endpoints = np.stack([start_i, end_i, start_j, end_j], axis=1)
    endpoint_on_other = np.stack([start_i_on_j,
                                  end_i_on_j,
                                  start_j_on_i,
                                  end_j_on_i],
                                 axis=1)
    has_touch = endpoint_on_other.any(axis=1)
    touch_point = candidate_endpoints[pair_ixs, np.argmax(endpoint_on_other, axis=1)]

    # ignore touche points already accounted for as overlaps, degenerate
    # cases, proper crossings
    is_touch = has_touch & ~is_overlap & ~is_degenerate & ~is_proper_crossing

    contributes_point = is_proper_crossing | is_touch
    intersection_point = np.where(is_proper_crossing[:, None],
                                  crossing_point,
                                  touch_point)

    # exclude consecutive shared endpoints (path vertices) & shared
    # start/endpoints for closed path
    is_adjacent = (j == i + 1)
    is_closure_pair = bool(path_is_closed) & (i == 0) & (j == num_segments - 1)
    is_trivial = ((is_adjacent & _same_point(intersection_point, start_j)) |
                  (is_closure_pair & _same_point(intersection_point, start_i)))
    keep = contributes_point & ~is_trivial

    # deduplicate crossing/touch locations
    kept_points = intersection_point[keep]
    if len(kept_points):
        snapped = np.round(kept_points / eps).astype(np.int64)
        num_distinct_points = np.unique(snapped, axis=0).shape[0]
    else:
        num_distinct_points = 0

    return int(num_distinct_points + np.count_nonzero(is_overlap))


def spatial_similarity(embeddings, orig_pdist):
    """
    Compute the correlation between pairwise distances among points in
    low-D embedding space and original high-D space.

    Parameters
    ----------
    embeddings: np.ndarray
        (N, 2) array of points in low-D space.
    orig_pdist: np.ndarray
        (N(N-1)/2,) array of precomputed pairwise distances in high-D space.

    Returns
    -------
    float
        Pearson correlation between high- and low-D pairwise distances.
    """
    emb_pdist = pdist(embeddings, metric='euclidean')

    emb_dev = emb_pdist - emb_pdist.mean()
    orig_dev = orig_pdist - orig_pdist.mean()
    return (emb_dev @ orig_dev) / np.sqrt(emb_dev @ emb_dev * orig_dev @ orig_dev)


EMBEDDINGS_DIR = config.DATA_DIR / 'embeddings'
SUBID_MAPPING = pd.read_csv(config.DATA_DIR / 'subid-mapping.csv',
                            index_col='Subject ID',
                            dtype_backend='numpy_nullable')

episode_events = np.load(config.DATA_DIR / 'episodes' / 'atlep1' / 'events.npy')

CENTERING_STRATEGY = int(sys.argv[1])
output_fpath = f'results_c{CENTERING_STRATEGY}.p'

if Path(output_fpath).is_file():
    sys.exit(0)


if CENTERING_STRATEGY == 0:
    orig_events = [episode_events]
    for rectype in ('atlep1', 'delayed'):
        avg_rec_events = np.load(config.DATA_DIR / 'participants' / 'average' / f'{rectype}_recall_events.npy')
        orig_events.append(avg_rec_events)
        for subid in SUBID_MAPPING.index:
            participant_dir = config.DATA_DIR / 'participants' / subid
            rec_events = np.load(participant_dir / f'{rectype}_recall_events.npy')
            orig_events.append(rec_events)
    orig_pdist_episode = pdist(episode_events, metric='cosine')

elif CENTERING_STRATEGY == 1:
    episode_events_centered = mean_center(episode_events)
    orig_events = [episode_events_centered]
    for rectype in ('atlep1', 'delayed'):
        avg_rec_events = np.load(config.DATA_DIR / 'participants' / 'average' / f'{rectype}_recall_events.npy')
        orig_events.append(mean_center(avg_rec_events))
        for subid in SUBID_MAPPING.index:
            participant_dir = config.DATA_DIR / 'participants' / subid
            rec_events = np.load(participant_dir / f'{rectype}_recall_events.npy')
            orig_events.append(mean_center(rec_events))
    orig_pdist_episode = pdist(episode_events_centered, metric='cosine')

elif CENTERING_STRATEGY == 2:
    episode_events_centered = mean_center(episode_events)
    rec_events_centered = {'atlep1': [], 'delayed': []}
    for subid in SUBID_MAPPING.index:
        participant_dir = config.DATA_DIR / 'participants' / subid
        imm_events = np.load(participant_dir / 'atlep1_recall_events.npy')
        del_events = np.load(participant_dir / 'delayed_recall_events.npy')
        imm_centered, del_centered = mean_center(imm_events, del_events)
        rec_events_centered['atlep1'].append(imm_centered)
        rec_events_centered['delayed'].append(del_centered)
    orig_events = [episode_events_centered]
    for rectype in ('atlep1', 'delayed'):
        avg_rec_events = np.load(config.DATA_DIR / 'participants' / 'average' / f'{rectype}_recall_events.npy')
        orig_events.append(mean_center(avg_rec_events))
        orig_events.extend(rec_events_centered[rectype])
    orig_pdist_episode = pdist(episode_events_centered, metric='cosine')

elif CENTERING_STRATEGY == 3:
    episode_events_centered = mean_center(episode_events)
    all_rec_events = []
    for rectype in ('atlep1', 'delayed'):
        for subid in SUBID_MAPPING.index:
            participant_dir = config.DATA_DIR / 'participants' / subid
            rec_events = np.load(participant_dir / f'{rectype}_recall_events.npy')
            all_rec_events.append(rec_events)
    mean_centroid = np.mean([r.mean(axis=0) for r in all_rec_events], axis=0)
    orig_events = [episode_events_centered]
    all_recs_ix = 0
    for rectype in ('atlep1', 'delayed'):
        avg_rec_events = np.load(config.DATA_DIR / 'participants' / 'average' / f'{rectype}_recall_events.npy')
        orig_events.append(avg_rec_events - mean_centroid)
        for _ in SUBID_MAPPING.index:
            orig_events.append(all_rec_events[all_recs_ix] - mean_centroid)
            all_recs_ix += 1
    orig_pdist_episode = pdist(episode_events_centered, metric='cosine')

orig_pdist_all = pdist(np.vstack(orig_events), metric='cosine')

results = []
for n_neighbors, min_dist, spread, random_seed in itertools.product(
    config.N_NEIGHBORS_VALS,
    np.arange(*config.MIN_DIST_ARANGE).round(1),
    range(*config.SPREAD_RANGE),
    range(*config.RANDOM_STATE_RANGE)
):
    filename = f'nn{n_neighbors}_md{min_dist}_sp{spread}_rs{random_seed}_c{CENTERING_STRATEGY}.npy'
    embeddings = np.load(EMBEDDINGS_DIR / filename)
    episode_embedding = embeddings[:episode_events.shape[0]]

    n_intersections = n_self_intersections(episode_embedding)
    spatial_corr_episode = spatial_similarity(episode_embedding, orig_pdist_episode)
    spatial_corr_all = spatial_similarity(embeddings, orig_pdist_all)

    results.append((filename,
                    n_neighbors,
                    min_dist,
                    spread,
                    random_seed,
                    CENTERING_STRATEGY,
                    n_intersections,
                    spatial_corr_episode,
                    spatial_corr_all))

df = pd.DataFrame(results, columns=('filename',
                                    'n_neighbors',
                                    'min_dist',
                                    'spread',
                                    'random_seed',
                                    'centering_strategy',
                                    'n_intersections',
                                    'spatial_corr_ep',
                                    'spatial_corr_all'))
df.to_pickle(output_fpath)

if (
        all(Path(f'results_c{cs}.p').is_file() for cs in config.CENTERING_STRATEGIES) and
        not Path('results.p').is_file()
):
    dfs = []
    for cs in config.CENTERING_STRATEGIES:
        dfs.append(pd.read_pickle(f'results_c{cs}.p'))
    full_df = pd.concat(dfs, axis=0, ignore_index=True)
    full_df.to_pickle('results.p')
