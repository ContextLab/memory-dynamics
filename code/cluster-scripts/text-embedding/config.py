from os import getenv
from pathlib import Path

import torch


# paths
BASE_DIR = Path(f'/home/{getenv("USER")}/memory-dynamics')
DATA_DIR = BASE_DIR / 'data'
RAW_DIR = DATA_DIR / 'raw'
PROCESSED_DIR = DATA_DIR / 'processed'

# paramters
EMBEDDING_MODEL_NAME = 'google/embeddinggemma-300m'
MIN_GPU_MEM_GB = 1
MAX_GPUS = 6
VERBOSE = True


# shared functions
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
