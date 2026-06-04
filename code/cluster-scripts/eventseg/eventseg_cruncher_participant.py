import pickle
import sys

import numpy as np

import eventseg_config as config
from eventseg_shared import search_segmentations


PARTICIPANT_ID, RECTYPE = sys.argv[1], sys.argv[2]

PARTICIPANT_DATA_DIR = config.DATA_DIR.joinpath('participants', PARTICIPANT_ID)
EPISODE_DATA_DIR = config.DATA_DIR.joinpath('episodes', 'atlep1')

fit_lda = pickle.loads(EPISODE_DATA_DIR.joinpath('fit_lda.p').read_bytes())
active_topics = fit_lda.components_.var(axis=1).nonzero()[0]

full_recall_trajectory = np.load(
        PARTICIPANT_DATA_DIR.joinpath(f'{RECTYPE}_full_recall_trajectory.npy')
)
recall_trajectory = full_recall_trajectory[:, active_topics]
recall_trajectory /= recall_trajectory.sum(axis=1, keepdims=True)

wasserstein_dists, best_eventseg = search_segmentations(
    similarity_timeseries,
    config.MIN_K,
    MAX_K,
    config.N_SPLIT_MERGE_PROPOSALS,
    print_progress=True
)
np.save(PARTICIPANT_DATA_DIR.joinpath(f'{RECTYPE}_recall_eventseg_kvals.npy'),
        np.array(wasserstein_dists))
PARTICIPANT_DATA_DIR.joinpath(f'{RECTYPE}_recall_eventseg_model.p').write_bytes(
    pickle.dumps(best_eventseg)
)
