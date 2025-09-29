import inspect
from collections.abc import Mapping
from weakref import WeakKeyDictionary


class LazyDataDict(Mapping):
    """
    Helper class that enables dict-like access to various properties of
    the Participant class while retaining lazy loading/caching behavior
    on a per-item basis. Repr displays values for already-loaded
    properties and function objects for unloaded ones.
    """
    def __init__(self, instance, mapping):
        self._instance = instance
        self._mapping = dict(mapping)

    def __getitem__(self, key):
        return getattr(self._instance, self._mapping[key])

    def __iter__(self):
        return iter(self._mapping)

    def __len__(self):
        return len(self._mapping)

    def __repr__(self):
        items = {}
        for k, attr in self._mapping.items():
            if attr in self._instance.__dict__:
                items[k] = self._instance.__dict__[attr]
            else:
                fget = getattr(type(self._instance), attr).fget
                items[k] = fget

        return f"{self.__class__.__name__}({items!r})"


class Multiton(type):
    """
    Metaclass that enforces multiton behavior (single class instance per
    unique set of constructor args).
    """
    # track instances and cache signatures by class in weak-key dict
    _class_cache = WeakKeyDictionary()

    def __call__(cls, *args, **kwargs):
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
            # NOTE: this method of constructing keys requires all
            # arguments to `cls.__init__` are hashable.
            key = tuple(bound_args.arguments.items())[1:]

        if key not in instances:
            instances[key] = super().__call__(*args, **kwargs)

        return instances[key]