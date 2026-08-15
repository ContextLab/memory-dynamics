import pickle
import sys

import numpy as np
from brainiak.eventseg.event import EventSegment
from scipy.stats import wasserstein_distance

import eventseg_config as config


def proximal_diag_mask(event_mask):
    diag_mask = np.zeros_like(event_mask)
    rowcol_ixs = np.arange(diag_mask.shape[0])

    for k in range(1, diag_mask.shape[0]):
        kth_diag_ixs = (rowcol_ixs[:-k], rowcol_ixs[k:])
        if not (event_mask[kth_diag_ixs] > 0).any():
            break
        diag_mask[kth_diag_ixs] = True

    return diag_mask


def search_segmentations(
        trajectory: np.ndarray,
        min_k: int,
        max_k: int,
        n_split_merge_proposals: int,
        print_progress: bool = False
) -> tuple[list[float], EventSegment]:
    corrmat = np.corrcoef(trajectory)
    wasserstein_dists = []
    max_wd = 0

    n_events_range = np.arange(min_k, max_k + 1)

    for i, n_events in enumerate(n_events_range, start=1):
        hmm = EventSegment(n_events,
                        split_merge=True,
                        split_merge_proposals=n_split_merge_proposals)
        hmm.fit(trajectory)

        event_assignments = hmm.segments_[0] == hmm.segments_[0].max(axis=1, keepdims=True)
        event_mask = event_assignments @ event_assignments.T
        diag_mask = proximal_diag_mask(event_mask)

        within_corrs = corrmat[event_mask * diag_mask]
        across_corrs = corrmat[~event_mask * diag_mask]

        wd = wasserstein_distance(within_corrs, across_corrs)
        if wd > max_wd:
            max_wd = wd
            best_eventseg = hmm
        wasserstein_dists.append(wd)
        if print_progress:
            print(f'{i}/{len(n_events_range)}', flush=True)

    return wasserstein_dists, best_eventseg


EPISODE_DATA_DIR = config.DATA_DIR.joinpath('episodes', 'atlep1')

min_k = int(sys.argv[1])
max_k = int(sys.argv[2])

episode_trajectory = np.load(EPISODE_DATA_DIR.joinpath('trajectory.npy'))
episode_centered = episode_trajectory - episode_trajectory.mean(axis=0)

wasserstein_dists, best_eventseg = search_segmentations(
    episode_centered,
    min_k,
    max_k,
    config.N_SPLIT_MERGE_PROPOSALS,
    print_progress=True
)

np.save(EPISODE_DATA_DIR.joinpath(f'eventseg_kvals_{min_k}-{max_k}.npy'),
        np.array(wasserstein_dists))
EPISODE_DATA_DIR.joinpath(f'eventseg_model_{min_k}-{max_k}.p').write_bytes(
    pickle.dumps(best_eventseg))
