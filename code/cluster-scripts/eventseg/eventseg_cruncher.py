import pickle
import sys

import numpy as np
from brainiak.eventseg.event import EventSegment
from scipy.stats import wasserstein_distance

import eventseg_config as config


PARTICIPANT_ID, RECTYPE, MIN_K, MAX_K, N_SPLIT_MERGE_PROPOSALS = (
    sys.argv[1],
    sys.argv[2],
    int(sys.argv[3]),
    int(sys.argv[4]),
    int(sys.argv[5])
)


def proximal_diag_mask(event_mask):
    diag_mask = np.zeros_like(event_mask)
    rowcol_ixs = np.arange(diag_mask.shape[0])

    for k in range(1, diag_mask.shape[0]):
        kth_diag_ixs = (rowcol_ixs[:-k], rowcol_ixs[k:])
        if not (event_mask[kth_diag_ixs] > 0).any():
            break
        diag_mask[kth_diag_ixs] = True

    return diag_mask


PARTICIPANT_DATA_DIR = config.DATA_DIR.joinpath('participants', PARTICIPANT_ID)
EPISODE_DATA_DIR = config.DATA_DIR.joinpath('episodes', 'atlep1')

fit_lda = pickle.loads(EPISODE_DATA_DIR.joinpath('fit_lda.p').read_bytes())
active_topics = fit_lda.components_.var(axis=1).nonzero()[0]

full_recall_trajectory = np.load(
        PARTICIPANT_DATA_DIR.joinpath(f'{RECTYPE}_full_recall_trajectory.npy')
)
recall_trajectory = full_recall_trajectory[:, active_topics]
recall_trajectory /= recall_trajectory.sum(axis=1, keepdims=True)

recall_corrmat = np.corrcoef(recall_trajectory)
wasserstein_dists = []
max_wd = 0

for n_events in range(MIN_K, MAX_K + 1):
    hmm = EventSegment(n_events,
                       split_merge=True,
                       split_merge_proposals=N_SPLIT_MERGE_PROPOSALS)
    hmm.fit(recall_trajectory)

    event_assignments = hmm.segments_[0] == hmm.segments_[0].max(axis=1, keepdims=True)
    event_mask = np.dot(event_assignments, event_assignments.T)
    diag_mask = proximal_diag_mask(event_mask)

    within_corrs = recall_corrmat[event_mask * diag_mask]
    across_corrs = recall_corrmat[~event_mask * diag_mask]

    wd = wasserstein_distance(within_corrs, across_corrs)
    if wd > max_wd:
        max_wd = wd
        best_eventseg = hmm
    wasserstein_dists.append(wd)
    print(n_events)

np.save(PARTICIPANT_DATA_DIR.joinpath(f'{RECTYPE}_recall_eventseg_kvals.npy'),
        np.array(wasserstein_dists))
PARTICIPANT_DATA_DIR.joinpath(f'{RECTYPE}_recall_eventseg_model.p').write_bytes(
    pickle.dumps(best_eventseg)
)

print('finished')
