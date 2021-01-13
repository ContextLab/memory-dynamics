import pprint
from typing import TYPE_CHECKING, TypeVar

from IPython.core.oinspect import pylight, getsource as ipy_getsource
from IPython.display import display, DisplayHandle, HTML


_T = TypeVar('_T')


def show_source(obj: _T) -> DisplayHandle:
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
