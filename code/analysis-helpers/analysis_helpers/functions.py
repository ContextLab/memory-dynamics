import pprint
import re
import string
from typing import Dict

import numpy as np
import pandas as pd
from IPython.core.oinspect import pylight, getsource as ipy_getsource
from IPython.display import display, DisplayHandle, HTML
from nltk import pos_tag, word_tokenize
from nltk.stem import WordNetLemmatizer
from num2words import num2words

from analysis_helpers.constants import POS_MAPPING, STOP_WORDS, TEXT_SUBSTITUTIONS


########################################################################
#                          TEXT PREPROCESSING                          #
########################################################################
_lemmatizer = WordNetLemmatizer()


def format_text(text_ser: pd.Series):
    # ADD DOCSTRING
    # concat all features for given shot. Adding period as delimiter
    # helps POS tagger
    joined = '. '.join(list(text_ser.dropna()))
    # remove duplicate if one already existed
    joined = joined.replace('..', '.')
    # convert digits to words
    no_digit = re.sub(r"(\d+)", lambda x: num2words(int(x.group(0))), joined)
    lemmatized = lemmatize(no_digit)
    no_punc = lemmatized.translate(str.maketrans('', '', string.punctuation))    #re.sub("[^\w\s-]+", '', lemmatized.lower())
    # lowercase everything, remove stopwords, normalize spacing
    lower_list = no_punc.lower().split()
    return ' '.join(word for word in lower_list if word not in STOP_WORDS)


def lemmatize(text: str, pos_dict: Dict[str, str] = POS_MAPPING) -> str:
    # ADD DOCSTRING
    words_tags = pos_tag(word_tokenize(text))
    lemmas = []
    for word, tag in words_tags:
        lemma = _lemmatizer.lemmatize(word, pos_dict[tag[0]])
        lemmas.append(lemma)
    return ' '.join(lemmas)


def preprocess_text(data, /, data_type):
    # ADD DOCSTRING
    if data_type == 'episode':
        df = data.loc[:, 'Narrative details (external events)':'Setting']
    elif data_type == 'recall':
        df = pd.DataFrame(np.atleast_2d(data))
    else:
        raise ValueError(
            "Invalid value for 'data_type', must be either 'episode' or 'recall'"
        )

    # combine multi-word tokens, standardize names, replace euphemisms,
    # etc. **before** tokenizing & lemmatizing**
    df = df.replace(TEXT_SUBSTITUTIONS, regex=True)
    # meat of preprocessing happens in format_text
    words_bag = df.apply(format_text, axis=1).tolist()
    return words_bag[0].split() if data_type == 'recall' else words_bag



def show_source(obj: object) -> DisplayHandle:
    """
    Inspects an arbitrary object and displays its source code or
    definition as inline HTML in the notebook, with syntax highlighting
    applied. If the object is a module, class, method, property,
    function, traceback, frame, or code object, its source code is
    displayed. Otherwise, its '__repr__' formatted as HTML, highlighted,
    and pretty-printed.

    Parameters
    ----------
    obj : object
        The object to display.

    Returns
    -------
    obj_html: IPython.core.display.DisplayHandle
        The object's source code or definition is displayed inline in
        the notebook.

    Notes
    -----
    'IPython.core.oinspect.getsource' handles properties and objects
    defined in the same notebook as the call, while 'inspect.getsource'
    doesn't.

    """
    src = ipy_getsource(obj)
    if src is None:
        src = pprint.pformat(obj)
    # noinspection PyTypeChecker
    return display(HTML(pylight(src)))
