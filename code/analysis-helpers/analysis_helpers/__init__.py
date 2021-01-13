from pathlib import Path

from IPython.display import display, Markdown

from analysis_helpers.episode import Episode
from analysis_helpers.participant import Participant


def _imported_from_notebook() -> bool:
    """
    Returns True if the package is being imported from inside a Jupyter
    notebook, otherwise False.
      - 'get_ipython' function exists in global namespace if the import
        call came from any IPython environment (notebook, shell,
        console, etc.)
      - 'IPKernelApp' instance exists in IPython config only if running
        in a notebook
      - IPython config object is a 'traitlets.config', which acts like
        'collections.defaultdict' and inserts missing keys on indexing
        rather than throw a KeyError, so 'dict.__getitem__()' is used
        instead
    """
    try:
        dict.__getitem__(get_ipython().config, 'IPKernelApp')
    except (NameError, KeyError):
        return False
    else:
        return True


def _display_message() -> None:
    """
    For the sake of transparency in the analyses, any time analysis
    analysis functions/other objects imported from 'analysis_helpers'
    rather than defined in the notebook, displays a brief message at the
    bottom of the import cell with a link to the package on GitHub how
    to show the source code in the notebook directly

    """

    github_link = "https://github.com/ContextLab/memory-dynamics/tree/" \
                  "master/code/analysis-helpers"
    pkg_dir = Path(__file__).resolve().parent
    message = Markdown(
        "Experiment & Participant classes, helper functions, and "
        "variables used across multiple notebooks can be found in "
        f"`{pkg_dir}`, or on GitHub, [here]({github_link}).<br />You "
        "can also view source code directly from the notebook with:"
        "<br /><pre>    from analysis_helpers.functions import "
        "show_source<br />    show_source(foo)</pre>"
    )
    # noinspection PyTypeChecker
    display(message)


version_info = (0, 0, 1)
__version__ = '.'.join(map(str, version_info))


if _imported_from_notebook():
    _display_message()
