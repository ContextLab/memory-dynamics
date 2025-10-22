import re
from pathlib import Path

from nltk.corpus import stopwords


CONTENT_WARNING = """\
⚠️ The episodes of [*Atlanta*](https://en.wikipedia.org/wiki/Atlanta_(TV_series)) \
viewed by participants in this study explore themes of racism, homophobia, \
and other forms of discrimination. As a result, certain files in this \
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
PARTICIPANT_DATA_DIR = PROCESSED_DIR.joinpath('participants')


########################################################################
#                          TEXT PREPROCESSING                          #
########################################################################
STOP_WORDS = frozenset(stopwords.words('english')) | {
    # additional tokens that would be lemmatized to stop words
    "n't",     # -> "not"
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
    'like',
    'um',
    'umm',
    'hmm',
    'uh',
    'uhh',
    'huh',
    'oh',
    'yes',    # "no" already in NLTK stopwords corpus
    'yeah',
    'nah'
}

TEXT_SUBSTITUTIONS = {
    re.compile(pattern, flags=re.IGNORECASE): repl for pattern, repl in
    {
        # replace "smart quotes" with "dumb quotes"
        r'[“”]': '"',
        r'[‘’]': "'",
        # bigrams/trigrams to be tokenized as single unit
        r'\bd[ée]j[àa] vu\b': 'deja_vu',
        r'\bflo[- ]rid[ae]\b': 'Flo_Rida',
        r'\bt[- ]pain\b': 'T_Pain',
        r'\blow[- ]key\b': 'low_key',
        r'oj da juiceman': 'OJ_da_Juiceman',
        r'\bgucci mane\b': 'Gucci_Mane',
        r'\bfetty wap\b': 'Fetty_Wap',
        r'\bmobb deep\b': 'Mobb_Deep',
        # map alternate forms of characters' names, nicknames/pseudonyms,
        # actors' names, slight mispronunciations/inaccuracies/typos, etc.
        # to common form.
        r'\b(?:earnest|ernie|earnst|earl|(?:donald\s+)?glover|(?:childish\s+)?gambino)\b': 'Earn',
        r"\b(?:alfred paper boy|al(?:fred)?|alford|albert|playboy|(?<!')(?<!song |play )(?:paper|play)(?: boy(?: alfred)?| man)(?! song| on\b)|(?:paper|play) boy(?='s))\b": 'Alfred_Paper_Boy',
        r'\b(?:darr?i?en|darrell|daryle|dario|dominic)\b': 'Darius',
        r'\b(?:vanessa|lan|venn?)\b': 'Van',
        r'\bdavid\b': 'Dave',
        r'\b(?:jp|kc|tp|kyle(?:\s+p)?)\b': 'KP',
        r'\b(?:swift|smith)\b': 'Swiff',
        r'\b(?:lonnie|lola)\b': 'Lottie',
        r'\brandall\b': 'Riley',
        r'\b(?:(?:re)?gina|gia)(?: simms)?\b': 'Gina_Simms',
        r'\b(?:george[- ]?michael|michael-george)\b': 'George_Michael',
        r'\b(?:g\.o\.b\.?|joe|george oscar(?: bluth)?)\b': 'GOB',
        r'\bmae\b': 'Maeby',
        r'\b(?:lill?y|lucy)\b': 'Lindsay',
        # TODO: should "robert" be allowed for "Tobias"? 
        r'\bcecile\b': 'Lucille',
        r'\bboosh\b': 'Bluth',
        r'\bfünke\b': 'Funke',
        r'\b(?:debat|debuke)\b': 'Dekalb',
        # expletives -- see CONTENT_WARNING above
        r'\b(?:niggas?|(?:the\s+)?n-word|racial\s+slurs?|(?:racist|offensive)\s+word)\b': 'n***a',
        r'\b(?:fag(?:got)?|(?:the\s+)?f-word)\b': 'f****t',
        # accepted English shortenings of words
        r"(\w+)in'(?!\w)": r'\1ing',
        r'\bgonna\b': 'going to',
        r'\bwanna\b': 'want to',
        r'\bkinda\b': 'kind of',
        r'\bsorta\b': 'sort of',
        r'\blotta\b': 'lot of',
        r'\bgotta\b': 'got to',
        # other words/phrases to consider equivalent
        r'\b(?:blunt \(marijuana cigar\)|(?:(?<!pepper )(?<!grass )joints?|blunts?|weed|pot(?!\s+belly))\b)': 'marijuana',
        r"(?:paper|play) boy(?= on\b| song)|(?<=play |song )paper boy(?!'s)|(?<=playing )paper boy(?!'s)|(?<=song, )paper boy(?!'s)": 'Paper_Boy_song',
        r"\bmuckin['g]?\b": 'muckin_song',
        r'\b106\.5|one oh? (?:five|six) point (?:five|seven)\b': 'one_o_six_point_five',
        r"\bdj(?:'?s|ing)?\b": 'DJ',
        r'\bcigarillos\b': 'cigars',
        r'\bswirlers\b': 'swishers',
        r'\buninteresting\b': 'not interesting',
        r'\b(?:prison|jailhouse)\b': 'jail',
        r'\btrans\b': 'transgender',
        r'\bhomosexuals?\b': 'gay',
        r'\b(?:x ?|double )x ?l\b': 'XXL',
        r"'?90s": 'nineties',
        r'\bdr\.': 'doctor',
        r'\bt-shirt\b': 'tee shirt',
        r'\ba\.?p\.?d\.?\b': 'APD',
        r'\bc\.?e\.?o\.?\b': 'CEO',
        r'\bh\.?o\.?o\.?p\.?\b': 'HOOP',
        r'\bs\.?e\.?c\.?\b': 'securities and exchange commission',
        r'\b(?:sun ?)?glasses\b': 'glasses',
        r'\bcause\b': 'because',
        r'\bafterwards\b': 'afterward',
        r'\bexecs?\b': 'executive'
        # TODO: map mother/mom, father/dad to same tokens?
    }.items()
}

# map Treebank POS tags to subset of Universal Dependencies tags
# accepted by lemminflect (NOUN, PROPN, VERB, ADJ, ADV, AUX)
POS_MAPPING = {
    'JJ': 'ADJ',
    'JJR': 'ADJ',
    'JJS': 'ADJ',
    'MD': 'AUX',
    'NN': 'NOUN',
    'NNS': 'NOUN',
    'NNP': 'PROPN',
    'NNPS': 'PROPN',
    'RB': 'ADV',
    'RBR': 'ADV',
    'RBS': 'ADV',
    'VB': 'VERB',
    'VBD': 'VERB',
    'VBG': 'VERB',
    'VBN': 'VERB',
    'VBP': 'VERB',
    'VBZ': 'VERB',
}

LEMMATIZER_EXCLUSIONS = {
    'treebank_tags': frozenset({
        '.', ',', "''", '``', ':', '(', ')',    # punctuation
        'CC',   # coordinating conjunction, always stopwords
        'CD',   # cardinal number, not lemmatizeable
        'EX',   # "existential 'there'", always literal "there"
        'FW',   # foreign word (really mis-tagged tokens)
        'POS',  # possessive ending
        'RP',   # particle
        'TO',   # literal "to"
        'UH'    # interjection
    }),
    # specific words to exclude from lemmatization
    # (commented words are not always correctly lemmatized, but appear
    # only in the recall transcripts so they don't affect the analyses)
    'words': frozenset({
        'adios',
        'annoyed',
        'atlanta',
        'broke',
        'cans',
        # 'chobani',
        'cortes',
        # 'cred',
        'dice',
        'downstairs',
        # 'fedora',
        'glasses',
        'houdini',
        'hundred',
        'interesting',
        'manus',
        'meaning',
        'marks',
        'nutella',
        'outburst',
        # 'paris',
        'prior',
        # 'refuse',
        'sideways',
        'something',
        'striped',
        # 'tiara',
        'texas',
        # 'thanksgiving',
        'tired',
        'unfinished',
        'upstairs',
        # 'yada'
    })
}


########################################################################
#                      TOPIC MODELING PARAMETERS                       #
########################################################################
EPISODE_WINDOW_SIZE = 50  # annotations
RECALL_WINDOW_SIZE = 200  # words

# timestamp of last video frame, used for interpolating timeseries
ENDFRAME_TIMES = {
    'atlep1': 1454.16,
    'atlep2': 1302.6,
    'arrdev': 1232.76
}

CV_PARAMS = {
    'strip_accents': 'ascii',
    'stop_words': None,  # stopword removal handled separately
    'token_pattern': r'\b\w[_*\w]*\b',  # allow single-character tokens, don't treat * or _ as separators
    'analyzer': 'word',
}

LDA_PARAMS = {
    'n_components': 100,
    'learning_method': 'batch',
    'random_state': 0
}