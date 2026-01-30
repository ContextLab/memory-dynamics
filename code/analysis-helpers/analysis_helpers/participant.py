from __future__ import annotations

import pickle
from functools import cached_property, wraps
from typing import ClassVar, Self, Literal, TYPE_CHECKING

import numpy as np
import pandas as pd

from analysis_helpers import Episode
from analysis_helpers.constants import (
    PARTICIPANT_DATA_DIR,
    PROCESSED_DIR,
    TRANSCRIPTIONS_DIR
)
from analysis_helpers.internals import LazyDataDict, Multiton, _get_event_bounds

if TYPE_CHECKING:
    from brainiak.eventseg.event import EventSegment


def exclude_participants(
        *,
        avg: bool = False,
        condition: Literal['A', 'B'] | None = None
):
    """
    Decorator for data properties not defined for certain Participant
    instances.

    Parameters
    ----------
    avg : bool, optional
        If True, accessing the decorated property on the "average
        participant" instance will raise an AttributeError.
    condition : {'A','B'}, optional
        If provided, accessing the decorated property on Participant 
        instances with the given `self.condition` value will raise an 
        AttributeError.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if avg and self.subid == 'average':
                raise AttributeError('not available for "average" Participant object')
            if condition is not None and self.condition == condition:
                unviewed_ep = 'arrdev' if condition == 'A' else 'atlep2'
                raise AttributeError(
                        f'Condition {condition} participant "{self.subid}" '
                        f'did not view {unviewed_ep}'
                )
            return func(self, *args, **kwargs)
        return wrapper
    return decorator


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
            'delayed': '_delayed_recall_transcript',
            'atlep2': '_atlep2_recall_transcript',
            'arrdev': '_arrdev_recall_transcript'
        })

        self.windows = LazyDataDict(self, {
            'atlep1': '_atlep1_recall_windows',
            'delayed': '_delayed_recall_windows',
            'atlep2': '_atlep2_recall_windows',
            'arrdev': '_arrdev_recall_windows'
        })

        self.full_trajectories = LazyDataDict(self, {
            'atlep1': '_atlep1_full_recall_trajectory',
            'delayed': '_delayed_full_recall_trajectory',
            'atlep2': '_atlep2_full_recall_trajectory',
            'arrdev': '_arrdev_full_recall_trajectory'
        })

        self.trajectories = LazyDataDict(self, {
            'atlep1': '_atlep1_recall_trajectory',
            'delayed': '_delayed_recall_trajectory',
            'atlep2': '_atlep2_recall_trajectory',
            'arrdev': '_arrdev_recall_trajectory'
        })
        
        self.events = LazyDataDict(self, {
            'atlep1': '_atlep1_recall_events',
            'delayed': '_delayed_recall_events',
            'atlep2': '_atlep2_recall_events',
            'arrdev': '_arrdev_recall_events'
        })
        
        self.eventseg_models = LazyDataDict(self, {
            'atlep1': '_atlep1_recall_eventseg_model',
            'delayed': '_delayed_recall_eventseg_model',
            'atlep2': '_atlep2_recall_eventseg_model',
            'arrdev': '_arrdev_recall_eventseg_model'
        })
        
        self.eventseg_kvals = LazyDataDict(self, {
            'atlep1': '_atlep1_recall_eventseg_kvals',
            'delayed': '_delayed_recall_eventseg_kvals',
            'atlep2': '_atlep2_recall_eventseg_kvals',
            'arrdev': '_arrdev_recall_eventseg_kvals'
        })
        
        self.event_bounds = LazyDataDict(self, {
            'atlep1': '_atlep1_recall_event_bounds',
            'delayed': '_delayed_recall_event_bounds',
            'atlep2': '_atlep2_recall_event_bounds',
            'arrdev': '_arrdev_recall_event_bounds'
        })

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.subid!r})'

    ########################### TRANSCRIPTS ############################
    @cached_property
    @exclude_participants(avg=True)
    def _atlep1_recall_transcript(self) -> str:
        return TRANSCRIPTIONS_DIR.joinpath(
                self.subid, self.ses1_id, f'{self.ses1_id}-recall.txt'
        ).read_text()

    @cached_property
    @exclude_participants(avg=True)
    def _delayed_recall_transcript(self) -> str:
        return TRANSCRIPTIONS_DIR.joinpath(
                self.subid, self.ses2_id, f'{self.ses2_id}-delayed.txt'
        ).read_text()

    @cached_property
    @exclude_participants(avg=True, condition='B')
    def _atlep2_recall_transcript(self) -> str:
        return TRANSCRIPTIONS_DIR.joinpath(
                self.subid, self.ses2_id, f'{self.ses2_id}-recall.txt'
        ).read_text()

    @cached_property
    @exclude_participants(avg=True, condition='A')
    def _arrdev_recall_transcript(self) -> str:
        return TRANSCRIPTIONS_DIR.joinpath(
                self.subid, self.ses2_id, f'{self.ses2_id}-recall.txt'
        ).read_text()

    ############################# WINDOWS ##############################
    @cached_property
    @exclude_participants(avg=True)
    def _atlep1_recall_windows(self) -> np.ndarray:
        return np.load(self.data_dir.joinpath('atlep1_recall_windows.npy'))

    @cached_property
    @exclude_participants(avg=True)
    def _delayed_recall_windows(self) -> np.ndarray:
        return np.load(self.data_dir.joinpath('delayed_recall_windows.npy'))

    @cached_property
    @exclude_participants(avg=True, condition='B')
    def _atlep2_recall_windows(self) -> np.ndarray:
        return np.load(self.data_dir.joinpath('atlep2_recall_windows.npy'))

    @cached_property
    @exclude_participants(avg=True, condition='A')
    def _arrdev_recall_windows(self) -> np.ndarray:
        return np.load(self.data_dir.joinpath('arrdev_recall_windows.npy'))

    ######################## FULL TRAJECTORIES #########################
    @cached_property
    def _atlep1_full_recall_trajectory(self) -> np.ndarray:
        return np.load(self.data_dir.joinpath('atlep1_full_recall_trajectory.npy'))

    @cached_property
    def _delayed_full_recall_trajectory(self) -> np.ndarray:
        return np.load(self.data_dir.joinpath('delayed_full_recall_trajectory.npy'))

    @cached_property
    @exclude_participants(condition='B')
    def _atlep2_full_recall_trajectory(self) -> np.ndarray:
        return np.load(self.data_dir.joinpath('atlep2_full_recall_trajectory.npy'))

    @cached_property
    @exclude_participants(condition='A')
    def _arrdev_full_recall_trajectory(self) -> np.ndarray:
        return np.load(self.data_dir.joinpath('arrdev_full_recall_trajectory.npy'))

    ########################### TRAJECTORIES ###########################
    @cached_property
    def _atlep1_recall_trajectory(self) -> np.ndarray:
        episode = Episode('atlep1')
        trajectory = self._atlep1_full_recall_trajectory[:, episode.active_topics]
        return trajectory / trajectory.sum(axis=1, keepdims=True)

    @cached_property
    def _delayed_recall_trajectory(self) -> np.ndarray:
        episode = Episode('atlep1')
        trajectory = self._delayed_full_recall_trajectory[:, episode.active_topics]
        return trajectory / trajectory.sum(axis=1, keepdims=True)

    @cached_property
    def _atlep2_recall_trajectory(self) -> np.ndarray:
        episode = Episode('atlep2')
        trajectory = self._atlep2_full_recall_trajectory[:, episode.active_topics]
        return trajectory / trajectory.sum(axis=1, keepdims=True)

    @cached_property
    def _arrdev_recall_trajectory(self) -> np.ndarray:
        episode = Episode('arrdev')
        trajectory = self._arrdev_full_recall_trajectory[:, episode.active_topics]
        return trajectory / trajectory.sum(axis=1, keepdims=True)

    ############################## EVENTS ##############################
    @cached_property
    def _atlep1_recall_events(self) -> np.ndarray:
        return np.load(self.data_dir.joinpath('atlep1_recall_events.npy'))

    @cached_property
    def _delayed_recall_events(self) -> np.ndarray:
        return np.load(self.data_dir.joinpath('delayed_recall_events.npy'))

    @cached_property
    @exclude_participants(condition='B')
    def _atlep2_recall_events(self) -> np.ndarray:
        return np.load(self.data_dir.joinpath('atlep2_recall_events.npy'))

    @cached_property
    @exclude_participants(condition='A')
    def _arrdev_recall_events(self) -> np.ndarray:
        return np.load(self.data_dir.joinpath('arrdev_recall_events.npy'))

    ######################### EVENTSEG MODELS ##########################
    @cached_property
    @exclude_participants(avg=True)
    def _atlep1_recall_eventseg_model(self) -> EventSegment:
        return pickle.loads(
                self.data_dir.joinpath('atlep1_recall_eventseg_model.p').read_bytes()
        )

    @cached_property
    @exclude_participants(avg=True)
    def _delayed_recall_eventseg_model(self) -> EventSegment:
        return pickle.loads(
                self.data_dir.joinpath('delayed_recall_eventseg_model.p').read_bytes()
        )

    @cached_property
    @exclude_participants(avg=True, condition='B')
    def _atlep2_recall_eventseg_model(self) -> EventSegment:
        return pickle.loads(
                self.data_dir.joinpath('atlep2_recall_eventseg_model.p').read_bytes()
        )

    @cached_property
    @exclude_participants(avg=True, condition='A')
    def _arrdev_recall_eventseg_model(self) -> EventSegment:
        return pickle.loads(
                self.data_dir.joinpath('arrdev_recall_eventseg_model.p').read_bytes()
        )

    ################## EVENTSEG K-OPTIMIZATION VALUES ##################
    @cached_property
    @exclude_participants(avg=True)
    def _atlep1_recall_eventseg_kvals(self) -> np.ndarray:
        return np.load(self.data_dir.joinpath('atlep1_recall_eventseg_kvals.npy'))
    
    @cached_property
    @exclude_participants(avg=True)
    def _delayed_recall_eventseg_kvals(self) -> np.ndarray:
        return np.load(self.data_dir.joinpath('delayed_recall_eventseg_kvals.npy'))
    
    @cached_property
    @exclude_participants(avg=True, condition='B')
    def _atlep2_recall_eventseg_kvals(self) -> np.ndarray:
        return np.load(self.data_dir.joinpath('atlep2_recall_eventseg_kvals.npy'))
    
    @cached_property
    @exclude_participants(avg=True, condition='A')
    def _arrdev_recall_eventseg_kvals(self) -> np.ndarray:
        return np.load(self.data_dir.joinpath('arrdev_recall_eventseg_kvals.npy'))
    
    ######################### EVENT BOUNDARIES #########################
    @cached_property
    def _atlep1_recall_event_bounds(self) -> np.ndarray:
        return _get_event_bounds(self._atlep1_recall_eventseg_model)
    
    @cached_property
    def _delayed_recall_event_bounds(self) -> np.ndarray:
        return _get_event_bounds(self._delayed_recall_eventseg_model)
    
    @cached_property
    @exclude_participants(condition='B')
    def _atlep2_recall_event_bounds(self) -> np.ndarray:
        return _get_event_bounds(self._atlep2_recall_eventseg_model)
    
    @cached_property
    @exclude_participants(condition='A')
    def _arrdev_recall_event_bounds(self) -> np.ndarray:
        return _get_event_bounds(self._arrdev_recall_eventseg_model)
    