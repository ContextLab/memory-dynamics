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
        # r'\bfour twenty\b': 'four_twenty',
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
        r"'90s": 'nineties',
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

# words to exclude from lemmatization
# (commented words are not always correctly lemmatized, but only appear 
# in the recall transcripts so have no real impact)
LEMMATIZER_EXCLUSIONS = {
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
    # 'whereas',
    # 'worldstar',
    # 'yada'
}