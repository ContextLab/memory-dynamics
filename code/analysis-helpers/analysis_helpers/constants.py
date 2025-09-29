from pathlib import Path


########################################################################
#                                PATHS                                 #
########################################################################
DATA_DIR = Path('/mnt/data')

RAW_DIR = DATA_DIR.joinpath('raw')
ANNOTATIONS_DIR = RAW_DIR.joinpath('annotations')
TRANSCRIPTIONS_DIR = RAW_DIR.joinpath('transcriptions', 'manual')

PROCESSED_DIR = DATA_DIR.joinpath('processed')
EPISODE_DATA_DIR = PROCESSED_DIR.joinpath('models', 'episodes')
RECALL_DATA_DIR = PROCESSED_DIR.joinpath('models', 'recalls')