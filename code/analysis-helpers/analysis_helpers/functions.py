import re

from IPython.display import display, Markdown

from analysis_helpers.constants import CONTENT_WARNING
from analysis_helpers.internals import _imported_from_notebook


def show_content_warning() -> None:
    if _imported_from_notebook():
        display(Markdown(CONTENT_WARNING))
    else:
        plaintext_warning = re.sub(
                r"\[\*?(.+?)\*?]\(.+\)", r"\1", CONTENT_WARNING
        ).replace('&mdash;', '—')
        print(plaintext_warning)
