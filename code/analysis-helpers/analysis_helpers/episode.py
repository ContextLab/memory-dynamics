import pandas as pd

from analysis_helpers.constants import ANNOTATIONS_DIR, ENDFRAME_TIMES
from analysis_helpers.internals import lazy_data


class Episode:
    # ADD DOCSTRING
    def __init__(self, name):
        # ADD DOCSTRING
        self.name = name
        self.endframe_time = ENDFRAME_TIMES[name]

    @lazy_data
    def annotations(self) -> pd.DataFrame:
        return pd.read_csv(ANNOTATIONS_DIR.joinpath(f'{self.name}.csv'))
