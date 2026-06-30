import re

import matplotlib.pyplot as plt
import numpy as np
from IPython.display import display, Markdown
from matplotlib import font_manager

from analysis_helpers.constants import CONTENT_WARNING, FONTS_DIR
from analysis_helpers.internals import _imported_from_notebook


def mean_center(*to_center, equal_weight=True):
    """
    Mean-center one or more feature matrices by their shared centroid.

    Returns a tuple of inputs with the same shape & order as passed.
    """
    if len(to_center) == 1:
        return to_center[0] - to_center[0].mean(axis=0)

    input_was_1d = [x.ndim == 1 for x in to_center]
    to_center = [np.atleast_2d(x) for x in to_center]
    if equal_weight:
        mean_centroid = np.mean([x.mean(axis=0) for x in to_center], axis=0)
        centered = [x - mean_centroid for x in to_center]
    else:
        split_inds = np.cumsum([x.shape[0] for x in to_center])[:-1]
        stacked = np.vstack(to_center)
        stacked = stacked - stacked.mean(axis=0)
        centered = np.vsplit(stacked, split_inds)

    return tuple(c[0] if was_1d else c for c, was_1d in zip(centered, input_was_1d))


def set_figure_style():
    """
    Sets some helpful `matplotlib` options for figures generated for the
    paper. This gets called automatically whenever `analysis_helpers` is
    imported, but occasionally needs to be called again manually when
    some other function has overwritten the relevant
    `matplotlib.rcParams` (e.g., inside `seaborn.axes_style` context
    managers).
    """
    # embed text in PDFs for illustrator
    plt.rcParams['pdf.fonttype'] = 42

    # use Myriad Pro font, if available
    if FONTS_DIR.is_dir() and next(FONTS_DIR.iterdir(), None) is not None:
        # check whether the font has already been loaded by
        # `matplotlib`'s font manager
        # TODO: this is imperfect and only loads all Myriad Pro styles
        #  from FONTS_DIR if *no* Myriad Pro font is already loaded
        myriad_pro_fonts = [
            f for f in font_manager.fontManager.ttflist if f.name == 'Myriad Pro'
        ]
        if len(myriad_pro_fonts) == 0:
            for font_file in font_manager.findSystemFonts(fontpaths=[FONTS_DIR]):
                font_manager.fontManager.addfont(font_file)

        plt.rcParams['font.family'] = 'sans-serif'
        plt.rcParams['font.sans-serif'] = (
                ['Myriad Pro'] + plt.rcParams['font.sans-serif']
        )


def show_content_warning() -> None:
    if _imported_from_notebook():
        display(Markdown(CONTENT_WARNING))
    else:
        plaintext_warning = re.sub(
                r"\[\*?(.+?)\*?]\(.+\)", r"\1", CONTENT_WARNING
        ).replace('&mdash;', '—')
        print(plaintext_warning)
