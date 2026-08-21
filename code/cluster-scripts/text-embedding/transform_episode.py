import numpy as np
import pandas as pd
from scipy.interpolate import make_interp_spline
from sentence_transformers import SentenceTransformer

import config
from config import get_gpus, print_verbose


ANNOTATIONS_DIR = config.RAW_DIR / 'annotations'
OUTPUT_DIR = config.PROCESSED_DIR / 'episodes' / 'atlep1'

ENDFRAME_TIME = 1454.16  # seconds


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


def main():
    OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

    # Detect GPUs with sufficient free memory (need ~1GB for this model)
    free_gpus = get_gpus(config.MIN_GPU_MEM_GB, config.MAX_GPUS)

    # Load model and start multi-GPU pool on available GPUs only
    print_verbose(f'Loading model: {config.EMBEDDING_MODEL_NAME}...')
    model = SentenceTransformer(config.EMBEDDING_MODEL_NAME, device='cpu')
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
