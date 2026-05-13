import pickle
import sys

import numpy as np

import eventseg_config as config
from eventseg_shared import search_segmentations


MIN_K, MAX_K, N_SPLIT_MERGE_PROPOSALS = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])

EPISODE_DATA_DIR = config.DATA_DIR.joinpath('episodes', 'atlep1')

episode_trajectory = np.load(EPISODE_DATA_DIR.joinpath('trajectory.npy'))

wasserstein_dists, best_eventseg = search_segmentations(
    episode_trajectory, MIN_K, MAX_K, N_SPLIT_MERGE_PROPOSALS, print_progress=True
)
np.save(EPISODE_DATA_DIR.joinpath(f'eventseg_kvals.npy'), np.array(wasserstein_dists))
EPISODE_DATA_DIR.joinpath(f'eventseg_model.p').write_bytes(pickle.dumps(best_eventseg))
