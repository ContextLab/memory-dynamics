from pathlib import Path


# paths for loading & saving data & figures
DATA_DIR = Path('/mnt/data')
RAW_DIR = DATA_DIR.joinpath('raw')
ANNOTATIONS_DIR = RAW_DIR.joinpath('annotations')
TRANSCRIPTIONS_DIR = RAW_DIR.joinpath('transcriptions')
PROCESSED_DIR = DATA_DIR.joinpath('processed')
