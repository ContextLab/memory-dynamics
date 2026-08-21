from __future__ import annotations

import time
from typing import TYPE_CHECKING

import numpy as np

import eventseg_config as config

if TYPE_CHECKING:
    from pathlib import Path


def temp_kvals_files() -> list[Path]:
    files = EPISODE_DATA_DIR.glob('eventseg_kvals_*-*.npy')
    return sorted(files, key=lambda f: int(f.stem.split('_', 2)[2].split('-')[0]))


def temp_model_file(kvals_file: Path) -> Path:
    range_token = kvals_file.stem.split('_', 2)[2]
    return EPISODE_DATA_DIR / f'eventseg_model_{range_token}.p'


EPISODE_DATA_DIR = config.DATA_DIR / 'episodes' / 'atlep1'
POLL_INTERVAL = 60  # seconds

while True:
    kvals_files = temp_kvals_files()
    if (len(kvals_files) >= config.N_KVAL_RANGES
            and all(temp_model_file(f).is_file() for f in kvals_files)):
        break
    time.sleep(POLL_INTERVAL)

all_wasserstein_dists = []
best_max_wd = -np.inf
best_model_file = None
for kvals_file in kvals_files:
    wasserstein_dists = np.load(kvals_file)
    all_wasserstein_dists.append(wasserstein_dists)
    if wasserstein_dists.max() > best_max_wd:
        best_max_wd = wasserstein_dists.max()
        best_model_file = temp_model_file(kvals_file)

all_wasserstein_dists = np.concatenate(all_wasserstein_dists)
np.save(EPISODE_DATA_DIR.joinpath('eventseg_kvals.npy'), all_wasserstein_dists)

best_model_file.replace(EPISODE_DATA_DIR.joinpath('eventseg_model.p'))

for kvals_file in kvals_files:
    kvals_file.unlink(missing_ok=True)
    temp_model_file(kvals_file).unlink(missing_ok=True)    # best one was already moved
