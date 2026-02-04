from __future__ import annotations

import inspect
from collections.abc import Callable, Iterator, MutableMapping
from typing import TYPE_CHECKING
from weakref import WeakKeyDictionary

import numpy as np

if TYPE_CHECKING:
    from brainiak.eventseg.event import EventSegment

    from analysis_helpers.participant import Participant


class LazyDataDict(MutableMapping):
    """
    Helper class that enables dict-like access to various properties of
    the Participant class while retaining lazy loading/caching behavior
    on a per-item basis. Repr displays values for already-loaded
    properties and function objects for unloaded ones.
    """
    def __init__(self, instance: Participant, mapping: MutableMapping[str, str]) -> None:
        self._instance = instance
        self._mapping = dict(mapping)

    def __getitem__(self, key: str) -> str | Callable[[Participant], ...]:
        return getattr(self._instance, self._mapping[key])

    def __setitem__(self, key: str, value: str | Callable[[Participant], ...]) -> None:
        setattr(self._instance, self._mapping[key], value)

    def __delitem__(self, key: str) -> None:
        delattr(self._instance, self._mapping[key])

    def __iter__(self) -> Iterator[str]:
        return iter(self._mapping)

    def __len__(self) -> int:
        return len(self._mapping)

    def __repr__(self) -> str:
        items = {}
        for k, attr in self._mapping.items():
            if attr in self._instance.__dict__:
                items[k] = self._instance.__dict__[attr]
            else:
                items[k] = getattr(type(self._instance), attr).func

        return f"{self.__class__.__name__}({items!r})"


class Multiton(type):
    """
    Metaclass that enforces multiton behavior (single class instance per
    unique set of constructor args).
    """
    # track instances and cache signatures by class in weak-key dict
    _class_cache = WeakKeyDictionary()

    def __call__[T, **P](cls: type[T], *args: P.args, **kwargs: P.kwargs) -> T:
        if cls not in Multiton._class_cache:
            Multiton._class_cache[cls] = {
                'init_signature': inspect.signature(cls.__init__),
                'instances': {}
            }

        init_sig = Multiton._class_cache[cls]['init_signature']
        instances = Multiton._class_cache[cls]['instances']

        if cls.__init__ is object.__init__:
            key = ()
        else:
            # bind None to 'self' arg
            bound_args = init_sig.bind(None, *args, **kwargs)
            bound_args.apply_defaults()
            # exclude 'self' from key
            # Note: this method of constructing keys requires all
            # arguments to `cls.__init__` to be hashable.
            key = tuple(bound_args.arguments.items())[1:]

        if key not in instances:
            instances[key] = super().__call__(*args, **kwargs)

        return instances[key]


def _get_event_bounds(eventseg_model: EventSegment) -> np.ndarray:
    """
    Extract event boundaries given an EventSegment model.

    Parameters
    ----------
    eventseg_model : brainiak.eventseg.event.EventSegment
        Fit event segmentation model.

    Returns
    -------
    np.ndarray
        number-of-events x 2 matrix. Each row contains the index of the
        first and last trajectory timepoint comprising the given event.

    """
    labels = eventseg_model.segments_[0].argmax(axis=1)
    bounds_aug = np.flatnonzero(np.diff(labels, prepend=-1, append=-1))
    return np.column_stack((bounds_aug[:-1], bounds_aug[1:] - 1))


def _imported_from_notebook() -> bool:
    """
    Determine if the package was imported from inside Jupyter Notebook.

    Returns
    -------
    bool
        True if imported from Jupyter Notebook, False otherwise.

    Notes
    -----
    - `get_ipython` function exists in global namespace if running in
      any IPython environment (notebook, shell, console, etc.)
    - `IPKernelApp` instance exists in IPython config only if running
      in a notebook
    - IPython config object is a `traitlets.config.Config` instance:
      https://traitlets.readthedocs.io/en/stable/config-api.html#traitlets.config.Config
    """
    try:
        # noinspection PyUnresolvedReferences
        return get_ipython().config.has_key('IPKernelApp')
    except NameError:
        return False
