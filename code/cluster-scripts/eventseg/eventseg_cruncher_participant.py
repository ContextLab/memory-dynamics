import pickle
import sys

import numpy as np
from scipy.spatial.distance import cdist

import eventseg_config as config
from eventseg_shared import search_segmentations


PARTICIPANT_ID, RECTYPE = sys.argv[1], sys.argv[2]

EPISODE_DATA_DIR = config.DATA_DIR.joinpath('episodes', 'atlep1')
PARTICIPANT_DATA_DIR = config.DATA_DIR.joinpath('participants', PARTICIPANT_ID)

episode_events = np.load(EPISODE_DATA_DIR.joinpath('events.npy'))

recall_trajectory = np.load(PARTICIPANT_DATA_DIR.joinpath(f'{RECTYPE}_recall_trajectory.npy'))
recall_trajectory_centered = recall_trajectory - recall_trajectory.mean(axis=0)

similarity_timeseries = 1 - cdist(recall_trajectory_centered, episode_events, metric='cosine')

MAX_K = min(config.MAX_K, similarity_timeseries.shape[0])

wasserstein_dists, best_eventseg = search_segmentations(
    similarity_timeseries,
    config.MIN_K,
    MAX_K,
    config.N_SPLIT_MERGE_PROPOSALS,
    print_progress=True
)
np.save(PARTICIPANT_DATA_DIR.joinpath(f'{RECTYPE}_eventseg_kvals.npy'),
        np.array(wasserstein_dists))
PARTICIPANT_DATA_DIR.joinpath(f'{RECTYPE}_eventseg_model.p').write_bytes(
    pickle.dumps(best_eventseg)
)
