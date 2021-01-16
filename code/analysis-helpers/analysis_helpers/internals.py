from __future__ import annotations

import re
from typing import Dict
from functools import update_wrapper


from typing import Callable, Optional, overload, Type, TYPE_CHECKING, TypeVar, Union

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


class RegexReplacer(dict):
    # ADD DOCSTRING
    # exists so that replacement can be done on text corpora without
    # having to lowercase everything, which messes up the POS tagger
    def __init__(self, dict_: Dict[str, str]) -> None:
        # ADD DOCSTRING
        regex_dict = {
            re.compile(k, flags=re.I): v.capitalize() for k, v in dict_.items()
        }
        super().__init__(regex_dict)

    def __repr__(self):
        return dict.__repr__({k.pattern: v for k, v in self.items()})