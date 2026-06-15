import os
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from scipy.interpolate import make_interp_spline
from sentence_transformers import SentenceTransformer


# ======================================================================
#                             CONSTANTS
# ======================================================================
BASE_DIR = Path(f'/home/{os.getenv("USER")}/memory-dynamics')
ANNOTATIONS_DIR = BASE_DIR / 'data' / 'raw' / 'annotations'
OUTPUT_DIR = BASE_DIR / 'data' / 'processed' / 'episodes' / 'atlep1'

EMBEDDING_MODEL_NAME = 'google/embeddinggemma-300m'
MIN_GPU_MEM_GB = 1
MAX_GPUS = 6
ENDFRAME_TIME = 1454.16
VERBOSE = True

# ======================================================================
#                             FUNCTIONS
# ======================================================================
def print_verbose(*args, **kwargs) -> None:
    """Print progress updates if global VERBOSE variable is True"""
    if VERBOSE:
        print(*args, flush=True, **kwargs)


def get_gpus(min_mem_gb: float, max_gpus: int) -> list[str]:
    """Find up to max_gpus GPUs with at least min_mem_gb free memory"""
    min_free_bytes = min_mem_gb * 1024 ** 3
    free_gpus = []
    print_verbose('Checking GPU resources...')
    for i in range(torch.cuda.device_count()):
        free_mem, _ = torch.cuda.mem_get_info(i)
        free_gb = free_mem / 1024 ** 3
        if free_mem >= min_free_bytes:
            free_gpus.append(f'cuda:{i}')
            print_verbose(f'  GPU {i}: {free_gb:.1f} GB free — available')
        else:
            print_verbose(f'  GPU {i}: {free_gb:.1f} GB free — skipping (low memory)')

    if not free_gpus:
        raise RuntimeError('No GPUs with sufficient free memory found')

    if len(free_gpus) > max_gpus:
        skipped_gpus = free_gpus[max_gpus:]
        free_gpus = free_gpus[:max_gpus]
        print_verbose(f'  Capping at {max_gpus} GPUs; '
                      f'not using {", ".join(skipped_gpus)}')

    return free_gpus


def format_annotation(row: pd.Series) -> str:
    """
    Format a single shot's annotation fields for embedding.

    Includes narrative details (no prefix), speech/speaker/setting
    (with prefix). Excludes characters on screen, music, indoor/outdoor.
    """
    punctuation = {'.', '?', '!'}
    row = row.str.replace('"', '')
    formatted = []
    for col, prefix in (('Narrative details (external events)', None),
                        ('Narrative details (internal state)', None),
                        ('Speech', 'Dialogue'),
                        ('Character speaking', 'Speaker'),
                        ('Setting', 'Setting')):
        if pd.isna(col_content := row[col]):
            continue

        col_content = f'{col_content[0].upper()}{col_content[1:]}'
        if col_content[-1] not in punctuation:
            col_content = f'{col_content}.'

        if prefix is not None:
            if col == 'Speech':
                col_content = f'"{col_content}"'
            col_content = f'{prefix}: {col_content}'

        formatted.append(col_content)

    return ' '.join(formatted)


def resample_trajectory(
        trajectory: np.ndarray,
        timestamps: list[float],
        new_tmax: float,
        resolution: int = 1
) -> np.ndarray:
    """
    Resample trajectory to uniform time resolution via linear
    interpolation.
    """
    new_timepoints = np.arange(int(new_tmax) + resolution, step=resolution)
    spline = make_interp_spline(timestamps, trajectory, k=1, axis=0)
    resampled = spline(new_timepoints, extrapolate=False)
    # zero-order hold at boundaries
    resampled[new_timepoints < timestamps[0]] = trajectory[0]
    resampled[new_timepoints > timestamps[-1]] = trajectory[-1]
    return resampled


# ======================================================================
#                               MAIN
# ======================================================================
def main():
    OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

    # Detect GPUs with sufficient free memory (need ~1GB for this model)
    free_gpus = get_gpus(MIN_GPU_MEM_GB, MAX_GPUS)

    # Load model and start multi-GPU pool on available GPUs only
    print_verbose(f'Loading model: {EMBEDDING_MODEL_NAME}...')
    model = SentenceTransformer(EMBEDDING_MODEL_NAME, device='cpu')
    print_verbose(f'Starting multi-process pool on {len(free_gpus)} GPUs...')
    pool = model.start_multi_process_pool(target_devices=free_gpus)
    print_verbose(f'Started multi-process pool across {len(pool["processes"])} GPUs')

    try:
        annotations = pd.read_csv(ANNOTATIONS_DIR.joinpath('atlep1.csv'),
                                  dtype_backend='numpy_nullable')
        formatted_annotations = annotations.apply(format_annotation, axis=1).tolist()
        print_verbose('Computing embeddings...')
        shot_embeddings = model.encode_multi_process(formatted_annotations,
                                                     pool,
                                                     batch_size=256,
                                                     prompt_name='STS')
        midpoint_times = (
            annotations['Onset time'] +
            annotations['Onset time'].shift(-1, fill_value=ENDFRAME_TIME)
        ) / 2
        episode_trajectory = resample_trajectory(shot_embeddings,
                                                 timestamps=midpoint_times.tolist(),
                                                 new_tmax=ENDFRAME_TIME)
        np.save(OUTPUT_DIR.joinpath('annotations_trajectory.npy'), shot_embeddings)
        np.save(OUTPUT_DIR.joinpath('trajectory.npy'), episode_trajectory)

    finally:
        print_verbose('Cleaning up...')
        model.stop_multi_process_pool(pool)

    print_verbose('Done.')


if __name__ == '__main__':
    main()
