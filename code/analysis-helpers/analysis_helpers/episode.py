from __future__ import annotations

from functools import cached_property
from typing import Literal

import pandas as pd

from analysis_helpers.constants import ANNOTATIONS_DIR, ENDFRAME_TIMES
from analysis_helpers.internals import Multiton


class Episode(metaclass=Multiton):
    # ADD DOCSTRING
    def __init__(self, name: Literal['atlep1', 'atlep2', 'arrdev']) -> None:
        if name not in {'atlep1', 'atlep2', 'arrdev'}:
            raise ValueError(f"Invalid episode name: {name}")
        self.name = name
        self.endframe_time = ENDFRAME_TIMES[name]

    @cached_property
    def annotations(self) -> pd.DataFrame:
        return pd.read_csv(ANNOTATIONS_DIR.joinpath(f'{self.name}.csv'),
                           dtype_backend='numpy_nullable')