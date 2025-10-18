import re
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

STOP_WORDS = set(stopwords.words('english')) | {
    # tokens that appear in NLTK stopwords after lemmatization
    "'m",      # -> "be"
    "'re",     # -> "be"
    "'s",      # -> "be"
    "'ve",     # -> "have"
    "'d",      # -> "have"/"will"
    "'ll",     # -> "will"
    'would',   # -> "will"
    'could',   # -> "can"
    'done',    # -> "do"
    'others',  # -> "other"
    # other non-content/low-information words
    'okay',
    'ok',
    'like'
    'um',
    'umm',
    'uh',
    'uhh',
    'yes',
    'yeah',
    'nah'
}

TEXT_SUBSTITUTIONS = {
    re.compile(pattern, flags=re.IGNORECASE): repl for pattern, repl in
    {
        # bigrams/trigrams to be tokenized as single unit
        r'\bd[ée]ja +vu\b': 'deja_vu',
        r'\bflo[- ]rida\b': 'flo_rida',
        r'\bt[- ]pain\b': 't_pain',
        r'\blow[- ]key\b': 'low_key',
        # r'\bex[- ](?:girlfriend|wife)\b': 'ex_girlfriend',
        # 'parking lot': 'parking_lot',
        # 'night club': 'night_club',
        # 'ex girlfriend': 'ex_girlfriend', TODO: include "baby[- ]mama"?
        # 'ex-girlfriend': 'ex_girlfriend',
        # 'ex wife': 'ex_wife',
        # 'ex-wife': 'ex_wife',
        # map alternate forms of characters' names, nicknames/pseudonyms,
        # actors' names, slight mispronunciations/inaccuracies/typos, etc.
        # to common form.
        r'\b(?:earnest|ernie|earnst|earl|(?:donald\s+)?glover|(?:childish\s+)?gambino)\b': 'earn',
        r'\b(?:alfred paper boy|alfred|alford|albert|paper boy|play boy)\b': 'alfred_paper_boy',
        r'\b(?:darr?en|darrell|daryle|dario)\b': 'darius',
        r'\b(?:vanessa|lan|venn?)\b': 'van',
        r'\bdavid\b': 'dave',
        r'\b(?:jp|kyle(?:\s+p)?)\b': 'kp',
        r'\b(?:swift|smith)\b': 'swiff',
        r'\blonnie\b': 'lottie',
        r'\b(?:george[- ]?michael|michael-george)\b': 'george_michael',
        r'\bjoe\b': 'gob',
        r'\bmae\b': 'maeby',
        r'\blill?y\b': 'lindsay',
        r'\bcecile\b': 'lucille',
        r'\bboosh\b': 'bluth',
        # expletives -- see CONTENT_WARNING above
        r'\b(?:nigga|(?:the\s+)?n-word|racial\s+slurs?|(?:racist|offensive)\s+word)\b': 'n***a',
        r'\b(?:fag(?:got)?|(?:the\s+)?f-word)\b': 'f****t',
        # accepted English shortenings of words
        r"(\w+)in'(?!\w)": r'\1ing',
        r'\bgonna\b': 'going to',
        r'\bwanna\b': 'want to',
        r'\bkinda\b': 'kind of',
        r'\bsorta\b': 'sort of',
        r'\blotta\b': 'lot of',
        # other words/phrases to consider equivalent
        r'\b(?:joint|blunt(?: \(marijuana cigar\))?|weed|pot(?!\s+belly))\b': 'marijuana',
        r'\bcigarillos\b': 'cigars',
        r'\bhomosexuals?\b': 'gay'
    }.items()
}

# TODO: add "cause" to stop-words dict -- based on spot check, always used as "because" rather than verb