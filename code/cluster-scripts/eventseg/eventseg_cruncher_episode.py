import pickle

import numpy as np

import eventseg_config as config
from eventseg_shared import search_segmentations


EPISODE_DATA_DIR = config.DATA_DIR.joinpath('episodes', 'atlep1')

episode_trajectory = np.load(EPISODE_DATA_DIR.joinpath('trajectory.npy'))

wasserstein_dists, best_eventseg = search_segmentations(
    episode_trajectory,
    config.MIN_K,
    config.MAX_K,
    config.N_SPLIT_MERGE_PROPOSALS,
    print_progress=True
)
np.save(EPISODE_DATA_DIR.joinpath(f'eventseg_kvals.npy'), np.array(wasserstein_dists))
EPISODE_DATA_DIR.joinpath(f'eventseg_model.p').write_bytes(pickle.dumps(best_eventseg))
