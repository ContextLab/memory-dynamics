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
from sentence_transformers import SentenceTransformer

print('Done.', flush=True)

# =======================================================================
#                               PATHS
# =======================================================================
BASE_DIR = Path('/home/f0028ph/memory-dynamics')
TRANSCRIPTIONS_DIR = BASE_DIR / 'data' / 'raw' / 'transcriptions-formatted'
SUBID_MAPPING_PATH = BASE_DIR / 'data' / 'processed' / 'subid-mapping.csv'
OUTPUT_DIR = BASE_DIR / 'data' / 'processed' / 'participants'
STATUS_FILE = BASE_DIR / 'scripts' / '.transform_recalls_status.json'


# =======================================================================
#                             CONSTANTS
# =======================================================================
EMBEDDING_MODEL_NAME = 'google/embeddinggemma-300m'
RECALL_WINDOW_SIZE = 5  # sentences
MAX_GPUS = 6  # leave headroom to prevent overheating

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


def split_sentences(text: str) -> list[str]:
    """Split a text into sentences"""
    # split on sentence-ending punctuation (.!?) outside of quotes;
    # when sentence ends with a quote, include the closing quote
    sentence_pattern = r'(?:[^."!?]|"[^"]*"(?<![.!?]"))*(?:[.!?]|"[^"]*[.!?]")'
    return [s.strip() for s in re.findall(sentence_pattern, text)]


def parse_windows(textlist: list[str], wsize: int) -> list[str]:
    """Parse a list of strings into overlapping sliding windows"""
    windows = []
    for ix in range(1, wsize):
        windows.append(' '.join(textlist[:ix]))
    for ix in range(len(textlist)):
        windows.append(' '.join(textlist[ix : ix + wsize]))
    return windows


def write_status(status: dict) -> None:
    """Atomically write status JSON (write to temp file, then rename)."""
    tmp = STATUS_FILE.with_suffix('.tmp')
    tmp.write_text(json.dumps(status))
    tmp.rename(STATUS_FILE)


# =======================================================================
#                               MAIN
# =======================================================================
def main():
    # Load participant ID mapping
    id_mapping = pd.read_csv(
        SUBID_MAPPING_PATH,
        index_col='Subject ID',
        dtype_backend='numpy_nullable'
    )

    n_participants = len(id_mapping)
    total_tasks = n_participants * 2

    # Build the full task list so the monitor knows what to expect
    tasks = []
    for sub_n in range(1, n_participants + 1):
        row = id_mapping.iloc[sub_n - 1]
        subid = row.name
        for rectype in ('atlep1', 'delayed'):
            tasks.append({'subid': subid, 'rectype': rectype})

    start_time = time.time()

    write_status({
        'state': 'loading_model',
        'start_time': start_time,
        'update_time': time.time(),
        'total': total_tasks,
        'completed': 0,
        'skipped': 0,
        'current': None,
        'stage': 'loading model & starting GPU pool',
        'n_windows': None,
        'tasks': tasks,
    })

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

    completed = 0
    skipped = 0

    try:
        for sub_n in range(1, n_participants + 1):
            row = id_mapping.iloc[sub_n - 1]
            subid = row.name
            ses1_id = row['session 1']
            ses2_id = row['session 2']

            p_output_dir = OUTPUT_DIR / subid
            p_output_dir.mkdir(parents=True, exist_ok=True)

            for rectype, ses_id, filename_suffix in [
                ('atlep1', ses1_id, '-recall.txt'),
                ('delayed', ses2_id, '-delayed.txt'),
            ]:
                traj_path = p_output_dir / f'{rectype}_recall_trajectory.npy'
                windows_path = p_output_dir / f'{rectype}_recall_windows.npy'

                # Skip if already completed
                if traj_path.exists() and windows_path.exists():
                    completed += 1
                    skipped += 1

                    write_status({
                        'state': 'running',
                        'start_time': start_time,
                        'update_time': time.time(),
                        'total': total_tasks,
                        'completed': completed,
                        'skipped': skipped,
                        'current': f'{rectype}, {subid}',
                        'stage': 'skipped (already exists)',
                        'n_windows': None,
                        'tasks': tasks,
                    })
                    continue

                # Load and preprocess transcript
                write_status({
                    'state': 'running',
                    'start_time': start_time,
                    'update_time': time.time(),
                    'total': total_tasks,
                    'completed': completed,
                    'skipped': skipped,
                    'current': f'{rectype}, {subid}',
                    'stage': 'preprocessing',
                    'n_windows': None,
                    'tasks': tasks,
                })
                transcript_path = (
                    TRANSCRIPTIONS_DIR / subid / ses_id / f'{ses_id}{filename_suffix}'
                )
                transcript = transcript_path.read_text()
                processed_transcript = preprocess_text(transcript)

                # Parse into sliding windows and embed
                sentence_list = split_sentences(processed_transcript)
                p_windows = parse_windows(
                    sentence_list, wsize=RECALL_WINDOW_SIZE
                )

                write_status({
                    'state': 'running',
                    'start_time': start_time,
                    'update_time': time.time(),
                    'total': total_tasks,
                    'completed': completed,
                    'skipped': skipped,
                    'current': f'{rectype}, {subid}',
                    'stage': 'embedding',
                    'n_windows': len(p_windows),
                    'tasks': tasks,
                })
                window_embeddings = model.encode_multi_process(
                    p_windows, pool, batch_size=256, prompt_name='STS'
                )

                # Save results immediately
                np.save(windows_path, np.array(p_windows))
                np.save(traj_path, window_embeddings)
                completed += 1

                write_status({
                    'state': 'running',
                    'start_time': start_time,
                    'update_time': time.time(),
                    'total': total_tasks,
                    'completed': completed,
                    'skipped': skipped,
                    'current': f'{rectype}, {subid}',
                    'stage': 'saved',
                    'n_windows': len(p_windows),
                    'tasks': tasks,
                })
    finally:
        model.stop_multi_process_pool(pool)

    write_status({
        'state': 'done',
        'start_time': start_time,
        'update_time': time.time(),
        'total': total_tasks,
        'completed': completed,
        'skipped': skipped,
        'current': None,
        'stage': 'finished',
        'n_windows': None,
        'tasks': tasks,
    })
    print('Done.')


if __name__ == '__main__':
    print('Running main function...', flush=True)
    main()
