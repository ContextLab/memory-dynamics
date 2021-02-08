from __future__ import annotations

from typing import Tuple

import pandas as pd

from analysis_helpers.constants import PROCESSED_DIR, TRANSCRIPTIONS_DIR
from analysis_helpers.internals import lazy_data, LazyDataDict, Multiton


class Participant(metaclass=Multiton):
    # ADD DOCSTRING
    ID_MAPPING: pd.DataFrame = pd.read_pickle(
        PROCESSED_DIR.joinpath('etc', 'subid_mapping.p')
    )

    @classmethod
    def load_all(cls) -> Tuple[Participant, ...]:
        # ADD DOCSTRING
        return tuple(cls(n) for n in range(1, len(cls.ID_MAPPING) + 1))

    @classmethod
    def from_subid(cls, subid: str) -> Participant:
        # ADD DOCSTRING
        try:
            sub_n = Participant.ID_MAPPING.index.get_loc(subid) + 1
        except KeyError as e:
            raise ValueError(f"No participant with Subject ID '{subid}'") from e
        else:
            return cls(sub_n=sub_n)

    @classmethod
    def from_sesid(cls, sesid: str) -> Participant:
        # ADD DOCSTRING
        row_mask = Participant.ID_MAPPING.eq(sesid).any(axis=1)
        try:
            subid = Participant.ID_MAPPING.index[row_mask][0]
        except IndexError as e:
            raise ValueError(f"No participant with session ID '{sesid}'") from e
        else:
            return cls.from_subid(subid=subid)

    def __init__(self, sub_n: int) -> None:
        # ADD DOCSTRING
        if sub_n not in range(1, len(Participant.ID_MAPPING) + 1):
            raise ValueError(
                "Participant indices range from 1 to "
                f"{len(Participant.ID_MAPPING)} (inclusive)"
            )
        self.sub_n = sub_n
        id_mapping_row = Participant.ID_MAPPING.iloc[sub_n - 1]
        self.subid = id_mapping_row.name
        self.ses1_id = id_mapping_row[0]
        self.ses2_id = id_mapping_row[1]
        self.group = 1 if 'A' in self.subid else 2

    ####################################################################
    #                        RECALL TRANSCRIPTS                        #
    ####################################################################
    @lazy_data
    def atlep1_recall_transcript(self) -> str:
        return TRANSCRIPTIONS_DIR.joinpath(
            self.subid, self.ses1_id, f'{self.ses1_id}-recall.txt'
        ).read_text()

    @lazy_data
    def delayed_recall_transcript(self) -> str:
        return TRANSCRIPTIONS_DIR.joinpath(
            self.subid, self.ses2_id, f'{self.ses2_id}-delayed.txt'
        ).read_text()

    @lazy_data
    def ses2_recall_transcript(self) -> str:
        return TRANSCRIPTIONS_DIR.joinpath(
            self.subid, self.ses2_id, f'{self.ses2_id}-recall.txt'
        ).read_text()

    @lazy_data
    def atlep1_recall_traj(self):
        ...

    # noinspection PyTypeChecker
    # (PyCharm's type checker doesn't recognize ses2_key as a valid
    # literal key TypedDict because of conditional)
    def _construct_attr_dicts(self) -> None:
        """
        provides alternate method for accessing data attributes that's
        sometimes more convenient (e.g., p.transcripts['atlep1'])
        """
        ses2_key = 'atlep2' if self.group == 1 else 'arrdev'
        # transcripts
        self.transcripts = LazyDataDict(self, {
                    'atlep1': 'atlep1_recall_transcript',
                    'delayed': 'delayed_recall_transcript',
                    ses2_key: 'ses2_recall_transcript'
                })
