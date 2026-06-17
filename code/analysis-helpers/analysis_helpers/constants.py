from pathlib import Path


CONTENT_WARNING = """\
⚠️ The episodes of [*Atlanta*](https://en.wikipedia.org/wiki/Atlanta_(TV_series)) \
viewed by participants in this study explore themes of racism, homophobia, \
and other forms of discrimination. As a result, certain files in this \
repository&mdash;possibly including this one&mdash;contain references to \
language that may be offensive or harmful. This language appears only in \
service of accurately representing and analyzing the stimuli and participants' \
responses, and its inclusion does not reflect an endorsement of its use by \
the authors."""

# timestamp of final frame of episode
ENDFRAME_TIME = 1454.16


########################################################################
#                                PATHS                                 #
########################################################################
DATA_DIR = Path('/mnt/data')

RAW_DIR = DATA_DIR.joinpath('raw')
ANNOTATIONS_DIR = RAW_DIR.joinpath('episode-annotations')
GOOGLE_FORM_DIR = RAW_DIR.joinpath('google-form-data')
PSITURK_DIR = RAW_DIR.joinpath('psiturk')
TRANSCRIPTS_DIR = RAW_DIR.joinpath('recall-transcripts')

PROCESSED_DIR = DATA_DIR.joinpath('processed')
EPISODE_DATA_DIR = PROCESSED_DIR.joinpath('episode')
PARTICIPANT_DATA_DIR = PROCESSED_DIR.joinpath('participants')

FONTS_DIR = DATA_DIR.joinpath('fonts')

FIG_DIR = Path('/mnt/paper/figures/source')


########################################################################
#                            FIGURE STYLING                            #
########################################################################
HEATMAP_CMAP = 'bone_r'
EVENTSEG_EDGECOLOR = '#FFF9AE'