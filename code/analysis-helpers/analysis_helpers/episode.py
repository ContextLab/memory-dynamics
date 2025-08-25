from typing import Literal

import pandas as pd

from analysis_helpers.constants import ANNOTATIONS_DIR, ENDFRAME_TIMES
from analysis_helpers.internals import lazy_data, Multiton


class Episode(metaclass=Multiton):
    # ADD DOCSTRING
    def __init__(self, name: Literal['atlep1', 'atlep2', 'arrdev']) -> None:
        # ADD DOCSTRING
        self.name = name
        self.endframe_time = ENDFRAME_TIMES[name]

    @lazy_data
    def annotations(self) -> pd.DataFrame:
        return pd.read_csv(ANNOTATIONS_DIR.joinpath(f'{self.name}.csv'))
