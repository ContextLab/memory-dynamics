import itertools
import sys
import warnings

import numpy as np
import pandas as pd
from umap import UMAP

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


RANDOM_SEED = int(sys.argv[1])
CENTERING_STRATEGY = int(sys.argv[2])

OUTPUT_DIR = config.DATA_DIR / 'embeddings'

SUBID_MAPPING = pd.read_csv(config.DATA_DIR / 'subid-mapping.csv',
                            index_col='Subject ID',
                            dtype_backend='numpy_nullable')

BASE_UMAP_PARAMS = {
    'n_components': 2,
    'metric': 'cosine',
    'output_metric': 'euclidean',
    'random_state': RANDOM_SEED,
    'verbose': False
}

episode_events = np.load(config.DATA_DIR / 'episodes' / 'atlep1' / 'events.npy')

if CENTERING_STRATEGY == 0:
    to_embed = [episode_events]
    for rectype in ('atlep1', 'delayed'):
        avg_rec_events = np.load(config.DATA_DIR / 'participants' / 'average' / f'{rectype}_recall_events.npy')
        to_embed.append(avg_rec_events)
        for subid in SUBID_MAPPING.index:
            participant_dir = config.DATA_DIR / 'participants' / subid
            rec_events = np.load(participant_dir / f'{rectype}_recall_events.npy')
            to_embed.append(rec_events)

elif CENTERING_STRATEGY == 1:
    to_embed = [mean_center(episode_events)]
    for rectype in ('atlep1', 'delayed'):
        avg_rec_events = np.load(config.DATA_DIR / 'participants' / 'average' / f'{rectype}_recall_events.npy')
        to_embed.append(mean_center(avg_rec_events))
        for subid in SUBID_MAPPING.index:
            participant_dir = config.DATA_DIR / 'participants' / subid
            rec_events = np.load(participant_dir / f'{rectype}_recall_events.npy')
            to_embed.append(mean_center(rec_events))

elif CENTERING_STRATEGY == 2:
    rec_events_centered = {'atlep1': [], 'delayed': []}
    for subid in SUBID_MAPPING.index:
        participant_dir = config.DATA_DIR / 'participants' / subid
        imm_events = np.load(participant_dir / 'atlep1_recall_events.npy')
        del_events = np.load(participant_dir / 'delayed_recall_events.npy')
        imm_centered, del_centered = mean_center(imm_events, del_events)
        rec_events_centered['atlep1'].append(imm_centered)
        rec_events_centered['delayed'].append(del_centered)
    to_embed = [mean_center(episode_events)]
    for rectype in ('atlep1', 'delayed'):
        avg_rec_events = np.load(config.DATA_DIR / 'participants' / 'average' / f'{rectype}_recall_events.npy')
        to_embed.append(mean_center(avg_rec_events))
        to_embed.extend(rec_events_centered[rectype])

elif CENTERING_STRATEGY == 3:
    all_rec_events = []
    for rectype in ('atlep1', 'delayed'):
        for subid in SUBID_MAPPING.index:
            participant_dir = config.DATA_DIR / 'participants' / subid
            rec_events = np.load(participant_dir / f'{rectype}_recall_events.npy')
            all_rec_events.append(rec_events)
    mean_centroid = np.mean([r.mean(axis=0) for r in all_rec_events], axis=0)
    to_embed = [mean_center(episode_events)]
    all_recs_ix = 0
    for rectype in ('atlep1', 'delayed'):
        avg_rec_events = np.load(config.DATA_DIR / 'participants' / 'average' / f'{rectype}_recall_events.npy')
        to_embed.append(avg_rec_events - mean_centroid)
        for _ in SUBID_MAPPING.index:
            to_embed.append(all_rec_events[all_recs_ix] - mean_centroid)
            all_recs_ix += 1

else:
    raise ValueError(f'Invalid value for centering strategy, {CENTERING_STRATEGY}')

warnings.filterwarnings(
    "ignore",
    message=".*n_jobs value 1 overridden to 1 by setting random_state. Use no seed for parallelism.*"
)

for n_neighbors, min_dist, spread in itertools.product(
    config.N_NEIGHBORS_VALS,
    np.arange(*config.MIN_DIST_ARANGE).round(1),
    range(*config.SPREAD_RANGE)
):
    output_fpath = (
        OUTPUT_DIR / f'nn{n_neighbors}_md{min_dist}_sp{spread}_rs{RANDOM_SEED}_c{CENTERING_STRATEGY}.npy'
    )
    if output_fpath.is_file():
        continue

    umap_params = BASE_UMAP_PARAMS.copy()
    umap_params.update({
        'n_neighbors': n_neighbors,
        'min_dist': min_dist,
        'spread': spread
    })

    reducer = UMAP(**umap_params)
    embeddings = reducer.fit_transform(np.vstack(to_embed))
    np.save(output_fpath, embeddings)
