from __future__ import annotations

import pickle
from functools import cached_property, wraps
from typing import ClassVar, Self, Literal

import numpy as np
import pandas as pd

from analysis_helpers import Episode
from analysis_helpers.constants import (
    PARTICIPANT_DATA_DIR,
    PROCESSED_DIR,
    TRANSCRIPTS_DIR
)
from analysis_helpers.internals import LazyDataDict, Multiton


def exclude_avg_participant(func):
    """
    Decorator for data properties not defined for the "average
    participant" instance.
    """
    @wraps(func)
    def wrapper(self, *args, **kwargs):
        if self.subid == 'average':
            raise AttributeError('not available for "average" Participant object')
        return func(self, *args, **kwargs)
    return wrapper


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
            'atlep1': '_atlep1_recall_transcript',
            'delayed': '_delayed_recall_transcript'
        })

        self.raw_transcripts = LazyDataDict(self, {
            'atlep1': '_raw_atlep1_recall_transcript',
            'delayed': '_raw_delayed_recall_transcript'
        })

        self.windows = LazyDataDict(self, {
            'atlep1': '_atlep1_recall_windows',
            'delayed': '_delayed_recall_windows'
        })

        self.trajectories = LazyDataDict(self, {
            'atlep1': '_atlep1_recall_trajectory',
            'delayed': '_delayed_recall_trajectory'
        })

        self.events = LazyDataDict(self, {
            'atlep1': '_atlep1_recall_events',
            'delayed': '_delayed_recall_events'
        })

        self.event_bounds = LazyDataDict(self, {
            'atlep1': '_atlep1_recall_event_bounds',
            'delayed': '_delayed_recall_event_bounds'
        })

        self.event_matches = LazyDataDict(self, {
            'atlep1': '_atlep1_recall_event_matches',
            'delayed': '_delayed_recall_event_matches'
        })

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.subid!r})'

    ######################### RAW TRANSCRIPTS ##########################
    @cached_property
    @exclude_avg_participant
    def _raw_atlep1_recall_transcript(self) -> str:
        return TRANSCRIPTS_DIR.joinpath(
            self.subid, self.ses1_id, f'{self.ses1_id}-recall-raw.txt'
        ).read_text()

    @cached_property
    @exclude_avg_participant
    def _raw_delayed_recall_transcript(self) -> str:
        return TRANSCRIPTS_DIR.joinpath(
            self.subid, self.ses2_id, f'{self.ses2_id}-delayed-raw.txt'
        ).read_text()

    ########################### TRANSCRIPTS ############################
    @cached_property
    @exclude_avg_participant
    def _atlep1_recall_transcript(self) -> str:
        return TRANSCRIPTS_DIR.joinpath(
                self.subid, self.ses1_id, f'{self.ses1_id}-recall-cleaned.txt'
        ).read_text()

    @cached_property
    @exclude_avg_participant
    def _delayed_recall_transcript(self) -> str:
        return TRANSCRIPTS_DIR.joinpath(
                self.subid, self.ses2_id, f'{self.ses2_id}-delayed-cleaned.txt'
        ).read_text()

    ############################# WINDOWS ##############################
    @cached_property
    @exclude_avg_participant
    def _atlep1_recall_windows(self) -> np.ndarray:
        return np.load(self.data_dir.joinpath('atlep1_recall_windows.npy'))

    @cached_property
    @exclude_avg_participant
    def _delayed_recall_windows(self) -> np.ndarray:
        return np.load(self.data_dir.joinpath('delayed_recall_windows.npy'))

    ########################### TRAJECTORIES ###########################
    @cached_property
    @exclude_avg_participant
    def _atlep1_recall_trajectory(self) -> np.ndarray:
        return np.load(self.data_dir.joinpath('atlep1_recall_trajectory.npy'))

    @cached_property
    @exclude_avg_participant
    def _delayed_recall_trajectory(self) -> np.ndarray:
        return np.load(self.data_dir.joinpath('delayed_recall_trajectory.npy'))

    ############################## EVENTS ##############################
    @cached_property
    def _atlep1_recall_events(self) -> np.ndarray:
        return np.load(self.data_dir.joinpath('atlep1_recall_events.npy'))

    @cached_property
    def _delayed_recall_events(self) -> np.ndarray:
        return np.load(self.data_dir.joinpath('delayed_recall_events.npy'))


    ################## EVENTSEG K-OPTIMIZATION VALUES ##################
    @cached_property
    @exclude_avg_participant
    def _atlep1_recall_eventseg_kvals(self) -> np.ndarray:
        return np.load(self.data_dir.joinpath('atlep1_recall_eventseg_kvals.npy'))

    @cached_property
    @exclude_avg_participant
    def _delayed_recall_eventseg_kvals(self) -> np.ndarray:
        return np.load(self.data_dir.joinpath('delayed_recall_eventseg_kvals.npy'))

    ######################### EVENT BOUNDARIES #########################
    @cached_property
    @exclude_avg_participant
    def _atlep1_recall_event_bounds(self) -> np.ndarray:
        return np.load(self.data_dir.joinpath('atlep1_recall_event_bounds.npy'))

    @cached_property
    @exclude_avg_participant
    def _delayed_recall_event_bounds(self) -> np.ndarray:
        return np.load(self.data_dir.joinpath('delayed_recall_event_bounds.npy'))

    ########################## EVENT MATCHES ###########################
    @cached_property
    def _atlep1_recall_event_matches(self) -> np.ndarray:
        return np.load(self.data_dir.joinpath('atlep1_recall_event_matches.npy'))

    @cached_property
    def _delayed_recall_event_matches(self) -> np.ndarray:
        return np.load(self.data_dir.joinpath('delayed_recall_event_matches.npy'))
