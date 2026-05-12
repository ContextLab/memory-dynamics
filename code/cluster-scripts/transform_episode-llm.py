if __name__ == '__main__':
    print('Importing libraries (main process)...', flush=True, end=' ')
else:
    print('Importing libraries (subprocess)...', flush=True, end=' ')


import json
import re
import time
from pathlib import Path

import numpy as np
import pandas as pd
import torch
from scipy.interpolate import make_interp_spline
from sentence_transformers import SentenceTransformer

print('Done.', flush=True)

# =======================================================================
#                               PATHS
# =======================================================================
BASE_DIR = Path('/home/f0028ph/memory-dynamics')
ANNOTATIONS_DIR = BASE_DIR / 'data' / 'raw' / 'annotations'
OUTPUT_DIR = BASE_DIR / 'data' / 'processed' / 'episodes' / 'atlep1'


# =======================================================================
#                             CONSTANTS
# =======================================================================
EMBEDDING_MODEL_NAME = 'google/embeddinggemma-300m'
EPISODE_WINDOW_SIZE = 1  # annotations
MAX_GPUS = 6  # leave headroom to prevent overheating
ENDFRAME_TIME = 1454.16

TEXT_SUBSTITUTIONS = {
    re.compile(pattern, flags=re.IGNORECASE): repl for pattern, repl in
    {
        # replace smart quotes with straight quotes
        r'[\u201c\u201d]': '"',
        r'[\u2018\u2019]': "'",
        # character name normalization (Atlanta)
#         r'\b(?:earnest|ernie|earnst|earl|(?:donald\s+)?glover|(?:childish\s+)?gambino)\b': 'Earn',
        r'\b(?:earn|ernie|earnst|earl|irv|(?:donald\s+)?glover|(?:childish\s+)?gambino)\b': 'Earnest',
#         r"\b(?:alfred paper boy|al(?:fred)?|alford|albert|playboy|(?<!')(?<!song |play )(?:paper|play)(?: boy(?: alfred)?| man)(?! song| on\b)|(?:paper|play) boy(?='s))\b": 'Alfred Paper Boy',
        r"\b(?:alfred paper boy|al(?:fred)?|alford|albert|playboy|(?<!')(?<!song |play )(?:paper|play)(?: boy(?: alfred)?| man)(?! song| on\b)|(?:paper|play) boy(?='s))\b": 'Alfred',
        r'\b(?:darr?i?en|darrell|daryle|dario|dominic)\b': 'Darius',
#         r'\b(?:vanessa|lan|fran|venn?)\b': 'Van',
        r'\b(?:van|lan|fran|venn?)\b': 'Vanessa',
        r'\bdavid\b': 'Dave',
        r'\b(?:jp|kc|tp|kyle(?:\s+p)?)\b': 'KP',
        r'\b(?:swift|smith)\b': 'Swiff',
        r'\b(?:lonnie|lola)\b': 'Lottie',
        r'\brandall\b': 'Riley',
        # expletives -- see content warning
#         r'\b(?:niggas?|(?:the\s+)?n-word|racial\s+slurs?|(?:racist|offensive)\s+word)\b': 'n***a',
        r'\b(?:niggers?|(?:the\s+)?n-word|racial\s+slurs?|(?:(?:an?|the)\s+)?(?:racist|offensive)\s+word)\b': 'nigga',
        # contraction expansion
        r"(\w+)in'(?!\w)": r'\1ing',
        r'\bgonna\b': 'going to',
        r'\bwanna\b': 'want to',
        r'\bkinda\b': 'kind of',
        r'\bsorta\b': 'sort of',
        r'\blotta\b': 'lot of',
        r'\bgotta\b': 'got to',
        r'\bcause\b': 'because',    # note: manually checked and all uses of "cause" == "because"
    }.items()
}


# =======================================================================
#                             FUNCTIONS
# =======================================================================
def preprocess_text(text: str) -> str:
    """Apply text substitutions"""
    for pattern, replacement in TEXT_SUBSTITUTIONS.items():
        text = pattern.sub(replacement, text)
    return ' '.join(text.split())


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


def parse_windows(textlist: list[str], wsize: int) -> list[str]:
    """Parse a list of strings into overlapping sliding windows"""
    windows = []
    for ix in range(1, wsize):
        windows.append(' '.join(textlist[:ix]))
    for ix in range(len(textlist)):
        windows.append(' '.join(textlist[ix : ix + wsize]))
    return windows


def get_midpoint_times(onsets, wsize, endframe_time):
    """
    Compute midpoint between onset of first annotation and offset of last
    annotation in each window.
    """
    midpoint_times = []
    for ix in range(1, wsize):
        midpoint_times.append(onsets[ix] / 2)
    for ix in range(len(onsets)):
        next_onset = onsets[ix + wsize] if ix + wsize < len(onsets) else endframe_time
        midpoint_times.append((onsets[ix] + next_onset) / 2)
    return midpoint_times


def resample_trajectory(
        trajectory: np.ndarray,
        timestamps: list[float],
        new_tmax: float,
        resolution: int = 1
) -> np.ndarray:
    """Resample trajectory to uniform time resolution via linear interpolation."""
    new_timepoints = np.arange(int(new_tmax) + resolution, step=resolution)
    spline = make_interp_spline(timestamps, trajectory, k=1, axis=0)
    resampled = spline(new_timepoints, extrapolate=False)
    # zero-order hold at boundaries
    resampled[new_timepoints < timestamps[0]] = trajectory[0]
    resampled[new_timepoints > timestamps[-1]] = trajectory[-1]
    return resampled


# =======================================================================
#                               MAIN
# =======================================================================
def main():
    # Load participant ID mapping

    # Detect GPUs with sufficient free memory (need ~1GB for this model)
    min_free_bytes = 1 * 1024 ** 3
    free_gpus = []
    for i in range(torch.cuda.device_count()):
        free_mem, _ = torch.cuda.mem_get_info(i)
        free_gb = free_mem / 1024 ** 3
        if free_mem >= min_free_bytes:
            free_gpus.append(f'cuda:{i}')
            print(f'  GPU {i}: {free_gb:.1f} GB free — available', flush=True)
        else:
            print(f'  GPU {i}: {free_gb:.1f} GB free — skipping (low memory)', flush=True)

    if not free_gpus:
        raise RuntimeError('No GPUs with sufficient free memory found')

    if len(free_gpus) > MAX_GPUS:
        skipped_gpus = free_gpus[MAX_GPUS:]
        free_gpus = free_gpus[:MAX_GPUS]
        print(f'  Capping at {MAX_GPUS} GPUs to prevent overheating; '
              f'not using {", ".join(skipped_gpus)}', flush=True)

    # Load model and start multi-GPU pool on available GPUs only
    print(f'Loading model: {EMBEDDING_MODEL_NAME}...', flush=True)
    model = SentenceTransformer(EMBEDDING_MODEL_NAME, device='cpu')
    print(f'Starting multi-process pool on {len(free_gpus)} GPUs...', flush=True)
    pool = model.start_multi_process_pool(target_devices=free_gpus)
    n_gpus = len(pool['processes'])
    print(f'Started multi-process pool across {n_gpus} GPUs', flush=True)

    try:
        annotations = pd.read_csv(
            ANNOTATIONS_DIR.joinpath('atlep1.csv'),
            dtype_backend='numpy_nullable'
        )

        formatted_annotations = (
            annotations
            .apply(format_annotation, axis=1)
            .apply(preprocess_text)
            .tolist()
        )

        episode_windows = parse_windows(
            formatted_annotations, wsize=EPISODE_WINDOW_SIZE
        )

        window_embeddings = model.encode_multi_process(
            episode_windows, pool, batch_size=256, prompt_name='STS'
        )

        midpoint_times = get_midpoint_times(
            annotations['Onset time'].tolist(),
            wsize=EPISODE_WINDOW_SIZE,
            endframe_time=1466.0
        )

        episode_trajectory = resample_trajectory(
            window_embeddings, timestamps=midpoint_times, new_tmax=ENDFRAME_TIME
        )

        np.save(OUTPUT_DIR.joinpath('trajectory.npy'), episode_trajectory)
        np.save(OUTPUT_DIR.joinpath('windows.npy'), episode_windows)

    finally:
        model.stop_multi_process_pool(pool)

    print('Done.')


if __name__ == '__main__':
    print('Running main function...', flush=True)
    main()
