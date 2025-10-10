from pathlib import Path


CONTENT_WARNING = """\
⚠️ The episodes of [*Atlanta*](https://en.wikipedia.org/wiki/Atlanta_(TV_series)) \
viewed by participants in this study explore themes of racism, homophobia, \
and other forms of discrimination. Consequently, certain files in this \
repository&mdash;possibly including this one&mdash;contain references to \
language that may be offensive or harmful. This language appears only in \
service of accurately representing and analyzing the stimuli and participants' \
responses, and its inclusion does not reflect an endorsement of its use by \
the authors."""


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
    'atlep1': 1454.16,
    'atlep2': 1302.6,
    'arrdev': 1232.76
}