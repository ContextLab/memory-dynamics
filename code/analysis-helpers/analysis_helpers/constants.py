from collections import defaultdict
from pathlib import Path

from nltk.corpus import stopwords

from analysis_helpers.internals import RegexReplacer


########################################################################
#                                PATHS                                 #
########################################################################
# paths for loading & saving data & figures
DATA_DIR = Path('/mnt/data')
RAW_DIR = DATA_DIR.joinpath('raw')
ANNOTATIONS_DIR = RAW_DIR.joinpath('annotations')
TRANSCRIPTIONS_DIR = RAW_DIR.joinpath('transcriptions', 'manual')
PROCESSED_DIR = DATA_DIR.joinpath('processed')
EPISODE_DATA_DIR = PROCESSED_DIR.joinpath('models', 'episodes')
RECALL_DATA_DIR = PROCESSED_DIR.joinpath('models', 'recalls')


########################################################################
#                      TOPIC MODELING PARAMETERS                       #
########################################################################
EPISODE_WSIZE = 50    # annotations
RECALL_WSIZE = 200    # words

CV_PARAMS = {
    'strip_accents': 'unicode',
    'stop_words': None    # stop words handled separately
}

LDA_PARAMS = {
    'n_components': 100,
    'learning_method': 'batch',
    'random_state': 0
}


# POS tag mapping, format: {Treebank tag (1st letter only): Wordnet}
POS_MAPPING = defaultdict(
    lambda: 'n',     # defaults to noun
    {
        'N': 'n',    # noun types
        'P': 'n',    # pronoun types, predeterminers
        'V': 'v',    # verb types
        'J': 'a',    # adjective types
        'D': 'a',    # determiner
        'R': 'r'     # adverb types
    }
)


# timestamp of last video frame, used for interpolating timeseries
ENDFRAME_TIMES = {
    'atlep1': 1466.0,
    'atlep2': 1316.52,
    'arrdev': 1236.6
}


STOP_WORDS = set(
    # nltk stopwords
    tuple(word.replace("'", '') for word in stopwords.words('english'))
    # selected scikit-learn stopwords
    + ('afterwards', 'another', 'anyone', 'anything', 'anyway', 'around',
       'back', 'cannot', 'cant', 'either', 'eg', 'else', 'even', 'example',
       'however', 'ie', 'itd', 'lot', 'many', 'may', 'much', 'neither',
       'nothing', 'others', 'per', 'since', 'something', 'thus', 'us',
       'whether', 'yet')
    # other frequently used filler words, contractions, and byproducts
    # of how the word tokenizer splits things
    + ('also', 'ca', 'like', 'lot', 'nt', 'stuff', 'super', 'ta', 'thats',
       'theyre', 'theyve', 'u', 'whatever''wo')
)


a_note_on_language = """\
The FX series *Atlanta* was created [with the explicit goal](https\
://www.vox.com/culture/2018/2/28/17059740/fx-atlanta-robbin-season-2-\
review) of making its audience uncomfortable. Creator, executive \
producer, and lead actor Donald Glover has described the show as a \
["Trojan Horse"](https://www.newyorker.com/magazine/2018/03/05/\
donald-glover-cant-save-you) designed to lure viewers in with the \
promise of a comedy about hip-hop music from a well known artist and \
comedian, then force its largely white TV audience "to really \
experience racism, to really feel what it's like to be black in \
America." In one particularly jarring scene from the pilot episode, \
Earn, the main character, asks a white friend of his from Princeton \
named Dave to play his cousin Alfred's song on the radio station where \
he's a DJ. Dave refuses because Earn is too poor to bribe him, but \
first recounts a story to which the punchline is him very casually \
using a racial slur. Later, Earn goads Dave into telling the story \
again in front of other Black characters, and Dave conspicuously \
substitutes the slur for "man."

In recounting the episode, participants naturally avoided repeating \
such offensive language themselves, despite clearly remembering its \
use. Because our approach to characterizing memory entails mapping \
between the explicit contents of experiences and verbal recalls, and \
because our annotations of the stimuli reflect their verbatim \
transcripts, we chose to substitute this offensive language for \
instances of euphemisms that clearly refer to its use.\

Racism exists in numerous modern forms, both obvious and non-obvious. 
For a perspective on historical and modern usage of the n-word see \
[this piece](https://www.tolerance.org/magazine/fall-2011/\
straight-talk-about-the-nword) in *Teaching Tolerance*.
"""


# words & multi-word phrases to be combined or considered equivalent,
# based on a few different criteria:
TEXT_SUBSTITUTIONS = RegexReplacer({
    # combine common multi-word phrases & names considered single units
    'paper boy': 'paperboy',
    'george-michael': 'georgemichael',
    'flo rida': 'floxrida',
    'low key': 'lowkey',
    'low-key': 'lowkey',
    'parking lot': 'parkinglot',
    'night club': 'nightclub',
    'ex girlfriend': 'exgirlfriend',
    'ex-girlfriend': 'exgirlfriend',
    'ex wife': 'exwife',
    'ex-wife': 'exwife',
    # characters' nicknames are equivalent to full names
    'earnest': 'earn',
    'vanessa': 'van',
    'david': 'dave',
    # main character sometimes referred to by actor's name or pseudonym
    'donald glover': 'earn',
    'glover': 'earn',
    'childish gambino': 'earn',
    'gambino': 'earn',
    # explatives -- **see 'a_note_on_language' above**
    'f-word': 'fuck',
    'n-word': 'nigga',
    'racial slur': 'nigga',
    'offensive term': 'nigga',
    # other words/phrases
    'déja': 'deja',
    ' cause ': ' because ',
    ' weed ': ' marijuana ',
    ' pot ': ' marijuana ',
    # accepted English shortenings of words
    'gonna': 'going to',
    'wanna': 'want to',
    'kinda': 'kind of',
    'sorta': 'sort of',
    # common, slight, allowable inaccuracies in characters' names
    'ernie': 'earn',
    'albert': 'alfred',
    'swift': 'swiff',
    'smith': 'swiff',
    'lonnie': 'lottie',
    ' lan ': ' van ',
    'JP': 'KP',
    'darren': 'darius',
    'darrell': 'darius',
    'joe': 'gob',
    ' mae ': 'maeby',
    'lily': 'lindsay',
    'lilly': 'lindsay'
})
