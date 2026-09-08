import re

import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

import config
from config import get_gpus, print_verbose


TRANSCRIPTIONS_DIR = config.RAW_DIR / 'transcriptions-formatted'
SUBID_MAPPING_PATH = config.PROCESSED_DIR / 'subid-mapping.csv'
OUTPUT_DIR = config.PROCESSED_DIR / 'participants'

RECALL_WINDOW_SIZE = 5  # sentences


def split_sentences(text: str) -> list[str]:
    """
    Split recall transcript into sentences, excluding sentence breaks
    inside multi-sentence quoted speech.
    """
    sentence_pattern = r"""
        (?:                                              # non-sentence-ending:
              Mr\.(?=\s)                                 #   "Mr." when followed by whitespace
            | \.(?=[A-Za-z0-9])                          #   period directly followed by a letter/digit
            | \.(?<=[A-Za-z]\.[A-Za-z]\.)(?=\s*\S)       #   final period of an abbreviation (i.e., a.k.a., etc.)
            | "[^"]*"(?<![.!?]")(?<![.!?]'")             #   quote whose contents don't end in sentence punct
            | "[^"]*[.!?]'?"(?![^A-Za-z]*(?:[A-Z]|$))    #   sentence-punct quote, but next letter is lowercase
            | [^."!?]                                    #   any other non-special character
        )*
        (?:                                              # sentence-ending:
              \.(?![A-Za-z0-9])                          #   period not followed by letter/digit
            | [!?]                                       #   exclamation or question
            | "[^"]*[.!?]'?"(?=[^A-Za-z]*(?:[A-Z]|$))    #   sentence-punct quote followed by uppercase or end-of-text
        )
    """
    return [s.strip() for s in re.findall(sentence_pattern, text, re.VERBOSE)]


def parse_windows(textlist: list[str], wsize: int) -> list[str]:
    """Parse a list of strings into overlapping sliding windows"""
    windows = []
    for ix in range(1, wsize):
        windows.append(' '.join(textlist[:ix]))
    for ix in range(len(textlist)):
        windows.append(' '.join(textlist[ix : ix + wsize]))
    return windows


def main():
    OUTPUT_DIR.mkdir(exist_ok=True, parents=True)

    # Load participant ID mapping
    id_mapping = pd.read_csv(SUBID_MAPPING_PATH,
                             index_col='Subject ID',
                             dtype_backend='numpy_nullable')
    n_participants = len(id_mapping)

    # Detect GPUs with sufficient free memory (need ~1GB for this model)
    free_gpus = get_gpus(config.MIN_GPU_MEM_GB, config.MAX_GPUS)

    # Load model and start multi-GPU pool on available GPUs only
    print_verbose(f'Loading model: {config.EMBEDDING_MODEL_NAME}...')
    model = SentenceTransformer(config.EMBEDDING_MODEL_NAME, device='cpu')
    print_verbose(f'Starting multi-process pool on {len(free_gpus)} GPUs...')
    pool = model.start_multi_process_pool(target_devices=free_gpus)
    print_verbose(f'Started multi-process pool across {len(pool["processes"])} GPUs')

    try:
        print_verbose('Computing embeddings...')
        for sub_n in range(1, n_participants + 1):
            row = id_mapping.iloc[sub_n - 1]
            subid: str = row.name
            ses1_id = row['session 1']
            ses2_id = row['session 2']

            p_output_dir = OUTPUT_DIR / subid
            p_output_dir.mkdir(exist_ok=True)

            for rectype, ses_id, filename_suffix in [
                ('atlep1', ses1_id, '-recall.txt'),
                ('delayed', ses2_id, '-delayed.txt'),
            ]:
                traj_path = p_output_dir / f'{rectype}_recall_trajectory.npy'
                windows_path = p_output_dir / f'{rectype}_recall_windows.npy'

                # Skip if already completed
                if traj_path.exists() and windows_path.exists():
                    continue

                print_verbose(f'  P{sub_n}, {rectype}')
                # Load and preprocess transcript
                transcript_path = (TRANSCRIPTIONS_DIR /
                                   subid /
                                   ses_id /
                                   f'{ses_id}{filename_suffix}')
                transcript = transcript_path.read_text()

                # Parse into sliding windows and embed
                sentence_list = split_sentences(transcript)
                p_windows = parse_windows(sentence_list, wsize=RECALL_WINDOW_SIZE)
                window_embeddings = model.encode_multi_process(p_windows,
                                                               pool,
                                                               batch_size=256,
                                                               prompt_name='STS')
                # Save results immediately
                np.save(windows_path, np.array(p_windows))
                np.save(traj_path, window_embeddings)

    finally:
        print_verbose('Cleaning up...')
        model.stop_multi_process_pool(pool)

    print_verbose('Done.')


if __name__ == '__main__':
    main()
