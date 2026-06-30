import re
from inspect import getsource

import matplotlib.pyplot as plt
import numpy as np
from IPython.core.oinspect import pylight
from IPython.display import display, HTML, Markdown
from matplotlib import font_manager

from analysis_helpers.constants import CONTENT_WARNING, FONTS_DIR
from analysis_helpers.internals import _imported_from_notebook


def format_stats(
    stat,
    p,
    stat_name,
    df=None,
    n_decimals_stat=3,
    n_decimals_p=3,
    p_min=0.001,
    sep='\n',
    bold=False
):
    """
    General function for formatting the test statistic and p-value from
    a statistical test for display in a `matplotlib.pyplot` plot.

    Parameters
    ----------
    stat, p : float
        The test statistic and associated p-value.
    stat_name : str
        The string used to describe the test statistic in the plot
        (e.g., 't', 'r', etc.).
    df : int, optional
        The degrees of freedom associated with the test statistic. If
        not None (default), this is displayed in parentheses immediately
        after the test statistic (e.g., "t(10) = ...").
    n_decimals_stat, n_decimals_p : int, optional
        The number of decimals (default: 3) to display for the test
        statistic and p-value (if greater than `p_min`), respectively.
    p_min : float, optional
        The smallest p-value (default: 0.001) to display. Lower p-values
        are displayed as "p < `p_min`".
    sep : str, optional
        The string separating the formatted test statistic and p-value
        (e.g., "\n", ", "). Default: "\n".
    bold : bool, optional
        Whether to bold the formatted text (default: False).

    Returns
    -------
    str
        The formatted output to display in the plot.
    """
    tex_it_wrapper = '\mathbfit' if bold else '\mathit'

    stat_name_fmt = f'{tex_it_wrapper}{{{stat_name}}}'

    stat_text_fmt = f' = {stat:.{n_decimals_stat}f}'
    if df is not None:
        stat_text_fmt = f'({df}) {stat_text_fmt}'

    p_fmt = f'{tex_it_wrapper}{{p}}'
    if p < p_min:
        p_text_fmt = f' < {p_min}'
    else:
        p_text_fmt = f' = {p:.{n_decimals_p}f}'

    if bold:
        stat_text_fmt = f'\\mathbf{{{stat_text_fmt}}}'
        p_text_fmt = f'\\mathbf{{{p_text_fmt}}}'

    return f'${stat_name_fmt}{stat_text_fmt}${sep}${p_fmt}{p_text_fmt}$'


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


def show_source(obj):
    try:
        src = getsource(obj)
    except TypeError:
        src = obj
    try:
        return HTML(pylight(src))
    except AttributeError:
        return src
