from __future__ import annotations

from functools import update_wrapper
from typing import Callable, Optional, overload, Type, TYPE_CHECKING, TypeVar, Union

import pandas as pd

from analysis_helpers.constants import ANNOTATIONS_DIR

if TYPE_CHECKING:
    _FgetReturn = TypeVar('_FgetReturn')
    _T = TypeVar('_T')


# noinspection PyPep8Naming
class lazy_data:
    # ADD DOCSTRING
    def __init__(self, fget: Callable[[_T], _FgetReturn]) -> None:
        # ADD DOCSTRING
        self.fget = fget
        # adopt decorated method's __name__, __doc__, etc. for owner cls
        update_wrapper(self, fget)

    @overload
    def __get__(self, instance: _T, owner: Type[_T]) -> _FgetReturn: ...
    @overload
    def __get__(self, instance: None, owner: Type[_T]) -> lazy_data: ...
    def __get__(
            self,
            instance: Optional[_T],
            owner: Optional[Type[_T]] = None
    ) -> Union[_FgetReturn, lazy_data]:
        if instance is None:
            # return wrapped method when called on owner class object
            return self
        attr_val = self.fget(instance)
        setattr(instance, self.name, attr_val)
        return attr_val

    def __set_name__(self, owner: Type[_T], name: str) -> None:
        self.name = name


class Episode:
    # ADD DOCSTRING
    def __init__(self, name):
        # ADD DOCSTRING
        self.name = name

    @lazy_data
    def annotations(self) -> pd.DataFrame:
        return pd.read_csv(ANNOTATIONS_DIR.joinpath(f'{self.name}.csv'))
