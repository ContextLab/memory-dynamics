from pathlib import Path


########################################################################
#                                PATHS                                 #
########################################################################
DATA_DIR = Path('/mnt/data')

RAW_DIR = DATA_DIR.joinpath('raw')
ANNOTATIONS_DIR = RAW_DIR.joinpath('annotations')
GOOGLE_FORM_DIR = RAW_DIR.joinpath('google-form-data')
PSITURK_DIR = RAW_DIR.joinpath('psiturk')
TRANSCRIPTIONS_DIR = RAW_DIR.joinpath('transcriptions')

PROCESSED_DIR = DATA_DIR.joinpath('processed')
EPISODE_DATA_DIR = PROCESSED_DIR.joinpath('episodes')
RECALL_DATA_DIR = PROCESSED_DIR.joinpath('recalls')


########################################################################
#                      TOPIC MODELING PARAMETERS                       #
########################################################################
# timestamp of last video frame, used for interpolating timeseries
ENDFRAME_TIMES = {
    'atlep1': 1466.0,
    'atlep2': 1316.52,
    'arrdev': 1236.6
}