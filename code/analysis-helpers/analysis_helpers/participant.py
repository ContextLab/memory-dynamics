from __future__ import annotations

from functools import cached_property
from typing import ClassVar, Self, Literal

import numpy as np
import pandas as pd

from analysis_helpers.constants import (
    PARTICIPANT_DATA_DIR, 
    PROCESSED_DIR, 
    TRANSCRIPTIONS_DIR
)
from analysis_helpers.internals import LazyDataDict, Multiton


class Participant(metaclass=Multiton):
    """
    Class that represents an individual participant and provides access
    to their data via attributes. Data sources are lazily loaded and
    cached on first access to keep instances as lightweight as possible.
    """
    id_mapping: ClassVar[pd.DataFrame] = pd.read_csv(
            PROCESSED_DIR.joinpath('subid-mapping.csv'),
            index_col='Subject ID',
            dtype_backend='numpy_nullable'
    )
    
    @classmethod
    def average(cls) -> Self:
        return cls('average')

    @classmethod
    def from_subid(cls, subid: str) -> Self:
        """
        Factory method for creating Participant instances from Subject
        IDs.

        Parameters
        ----------
        subid : str
            The participant's Subject ID (beginning with "MD-").

        Returns
        -------
        Participant
            A new instance of the Participant class.
        """
        try:
            sub_n = cls.id_mapping.index.get_loc(subid) + 1
        except KeyError as e:
            raise ValueError(
                    f'No participant found with Subject ID "{subid}"'
            ) from e
        return cls(sub_n)

    @classmethod
    def load_all(cls) -> tuple[Participant, ...]:
        """
        Create instances for all participants and return them as a tuple.

        Returns
        -------
        tuple of Participant
        """
        return tuple(cls(n) for n in range(1, cls.id_mapping.shape[0] + 1))

    def __init__(self, sub_n: int | Literal['average']) -> None:
        """
        Main constructor for the Participant class.

        Creates an object that provides access to an individual
        participant's data given their numeric index (see below). To
        create Participant instances directly from subject IDs, use the
        `Participant.from_subid()` factory method.

        Parameters
        ----------
        sub_n : int
            The **1-indexed** row-index of the participant in
            `subid-mapping.csv` (corresponds to the order in which
            participants were collected).
        """
        if sub_n == 'average':
            self.subid = 'average'
            self.ses1_id = None
            self.ses2_id = None
            self.condition = None
        else:
            if sub_n not in range(1, Participant.id_mapping.shape[0] + 1):
                raise ValueError(
                        'Participant indices range from 1 to '
                        f'{Participant.id_mapping.shape[0]} (inclusive).'
                )
            id_mapping_row = Participant.id_mapping.iloc[sub_n - 1]
            self.subid = id_mapping_row.name
            self.ses1_id = id_mapping_row['session 1']
            self.ses2_id = id_mapping_row['session 2']
            self.condition = self.subid.split('-')[2]
        self.sub_n = sub_n
        self.data_dir = PARTICIPANT_DATA_DIR.joinpath(self.subid)

        self.transcripts = LazyDataDict(self, {
            'atlep1': 'atlep1_recall_transcript',
            'delayed': 'delayed_recall_transcript',
            'atlep2': 'atlep2_recall_transcript',
            'arrdev': 'arrdev_recall_transcript'
        })
        
        self.windows = LazyDataDict(self, {
            'atlep1': 'atlep1_recall_windows',
            'delayed': 'delayed_recall_windows',
            'atlep2': 'atlep2_recall_windows',
            'arrdev': 'arrdev_recall_windows'
        })
        
        self.trajectories = LazyDataDict(self, {
            'atlep1': 'atlep1_recall_trajectory',
            'delayed': 'delayed_recall_trajectory',
            'atlep2': 'atlep2_recall_trajectory',
            'arrdev': 'arrdev_recall_trajectory'
        })

    ########################### TRANSCRIPTS ############################
    @cached_property
    def atlep1_recall_transcript(self) -> str:
        return TRANSCRIPTIONS_DIR.joinpath(
                self.subid, self.ses1_id, f'{self.ses1_id}-recall.txt'
        ).read_text()

    @cached_property
    def delayed_recall_transcript(self) -> str:
        return TRANSCRIPTIONS_DIR.joinpath(
                self.subid, self.ses2_id, f'{self.ses2_id}-delayed.txt'
        ).read_text()

    @cached_property
    def atlep2_recall_transcript(self) -> str:
        if self.condition == 'B':
            raise AttributeError(
                    f'Condition B participant "{self.subid}" did not view atlep2'
            )
        return TRANSCRIPTIONS_DIR.joinpath(
                self.subid, self.ses2_id, f'{self.ses2_id}-recall.txt'
        ).read_text()

    @cached_property
    def arrdev_recall_transcript(self) -> str:
        if self.condition == 'A':
            raise AttributeError(
                    f'Condition A participant "{self.subid}" did not view arrdev'
            )
        return TRANSCRIPTIONS_DIR.joinpath(
                self.subid, self.ses2_id, f'{self.ses2_id}-recall.txt'
        ).read_text()

    ############################# WINDOWS ##############################
    @cached_property
    def atlep1_recall_windows(self) -> np.ndarray:
        return np.load(self.data_dir.joinpath('atlep1_recall_windows.npy'))
    
    @cached_property
    def delayed_recall_windows(self) -> np.ndarray:
        return np.load(self.data_dir.joinpath('delayed_recall_windows.npy'))
    
    @cached_property
    def atlep2_recall_windows(self) -> np.ndarray:
        if self.condition == 'B':
            raise AttributeError(
                    f'Condition B participant "{self.subid}" did not view atlep2'
            )
        return np.load(self.data_dir.joinpath('atlep2_recall_windows.npy'))
    
    @cached_property
    def arrdev_recall_windows(self) -> np.ndarray:
        if self.condition == 'A':
            raise AttributeError(
                    f'Condition A participant "{self.subid}" did not view arrdev'
            )
        return np.load(self.data_dir.joinpath('arrdev_recall_windows.npy'))

    ########################### TRAJECTORIES ###########################
    @cached_property
    def atlep1_recall_trajectory(self) -> np.ndarray:
        return np.load(self.data_dir.joinpath('atlep1_recall_trajectory.npy'))
    
    @cached_property
    def delayed_recall_trajectory(self) -> np.ndarray:
        return np.load(self.data_dir.joinpath('delayed_recall_trajectory.npy'))
    
    @cached_property
    def atlep2_recall_trajectory(self) -> np.ndarray:
        if self.condition == 'B':
            raise AttributeError(
                    f'Condition B participant "{self.subid}" did not view atlep2'
            )
        return np.load(self.data_dir.joinpath('atlep2_recall_trajectory.npy'))
    
    @cached_property
    def arrdev_recall_trajectory(self) -> np.ndarray:
        if self.condition == 'A':
            raise AttributeError(
                    f'Condition A participant "{self.subid}" did not view arrdev'
            )
        return np.load(self.data_dir.joinpath('arrdev_recall_trajectory.npy'))
