from __future__ import annotations

import re
from functools import update_wrapper
from inspect import getcallargs


from typing import (Any, Callable, Dict, Literal, NoReturn, Optional, overload,
                    Tuple, Type, TYPE_CHECKING, TypedDict, TypeVar, Union)

if TYPE_CHECKING:
    from analysis_helpers import Participant

    _FgetReturn = TypeVar('_FgetReturn')
    _T = TypeVar('_T')

    class _LazyDataDictInput(TypedDict, total=False):
        atlep1: str
        delayed: str
        atlep2: str
        arrdev: str


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


class LazyDataDict(dict):
    # ADD DOCSTRING
    def __init__(
            self,
            inst: Participant,
            dict_: _LazyDataDictInput
    ) -> None:
        # ADD DOCSTRING
        super().__init__(dict_)
        self.owner_inst = inst
        self.owner_cls = inst.__class__

    def __getitem__(self, name: str) -> Any:
        return getattr(self.owner_inst, super().__getitem__(name))

    def __setitem__(self, name: str, value: Any) -> NoReturn:
        raise TypeError("'LazyDataDict' does not support item assignment")


class Multiton(type):
    # ADD DOCSTRING
    # mangle names just in case derived class uses one of these
    __instances: Dict[Union[Type[_T], Tuple[Type[_T], Tuple, ...]], _T] = dict()
    __inits: Dict[Type, Callable] = dict()

    def __init__(
            cls: Type[_T],
            name: str,
            bases: Tuple[Type, ...],
            namespace: Dict[str, Any]
    ) -> None:
        # ADD DOCSTRING
        super().__init__(name, bases, namespace)
        Multiton.__inits[cls] = namespace.get('__init__')

    def __call__(cls: Type[_T], *args, **kwargs):
        init = Multiton.__inits[cls]
        if init is None:
            key = cls
        else:
            callargs = getcallargs(init, None, *args, **kwargs)
            key = (cls, *tuple(callargs.items()))

        if key not in Multiton.__instances:
            Multiton.__instances[key] = super(Multiton, cls).__call__(*args, **kwargs)
        return Multiton.__instances[key]


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