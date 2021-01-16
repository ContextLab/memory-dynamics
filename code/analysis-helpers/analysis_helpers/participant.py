from __future__ import annotations

import pandas as pd

from analysis_helpers.episode import lazy_data
from analysis_helpers.constants import PROCESSED_DIR


class Participant:
    ID_MAPPING: pd.DataFrame = pd.read_pickle(
        PROCESSED_DIR.joinpath('etc', 'subid_mapping.p')
    )

    @classmethod
    def from_subid(cls, subid: str) -> Participant:
        try:
            sub_n = Participant.ID_MAPPING.index.get_loc(subid)
        except KeyError as e:
            raise ValueError(f"No participant with Subject ID '{subid}'") from e
        else:
            return cls(sub_n=sub_n)

    @classmethod
    def from_sesid(cls, sesid: str) -> Participant:
        row_mask = Participant.ID_MAPPING.eq(sesid).any(axis=1)
        try:
            subid = Participant.ID_MAPPING.index[row_mask][0]
        except IndexError as e:
            raise ValueError(f"No participant with session ID '{sesid}'") from e
        else:
            return cls.from_subid(subid=subid)

    def __init__(self, sub_n: int) -> None:
        self.sub_n = sub_n
        id_mapping_row = Participant.ID_MAPPING.iloc[sub_n - 1]
        self.subid = id_mapping_row.name
        self.ses1_id = id_mapping_row[0]
        self.ses2_id = id_mapping_row[1]
        self.group = 1 if 'A' in self.subid else 2

    @lazy_data
    def atlep1_recall_traj(self):
        ...


