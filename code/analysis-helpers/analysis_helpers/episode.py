from __future__ import annotations

import pickle
from functools import cached_property
from typing import Literal, TYPE_CHECKING

import numpy as np
import pandas as pd

from analysis_helpers.constants import (
    ANNOTATIONS_DIR, 
    ENDFRAME_TIMES,
    EPISODE_DATA_DIR
)
from analysis_helpers.internals import Multiton, _get_event_bounds

if TYPE_CHECKING:
    from brainiak.eventseg.event import EventSegment
    from sklearn.decomposition import LatentDirichletAllocation
    from sklearn.feature_extraction.text import CountVectorizer


class Episode(metaclass=Multiton):
    # ADD DOCSTRING
    def __init__(self, name: Literal['atlep1', 'atlep2', 'arrdev']) -> None:
        if name not in {'atlep1', 'atlep2', 'arrdev'}:
            raise ValueError(f"Invalid episode name: {name}")
        self.name = name
        self.endframe_time = ENDFRAME_TIMES[name]
        self.data_dir = EPISODE_DATA_DIR.joinpath(name)

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.name!r})'

    @property
    def active_topics(self):
        return self.fit_lda.components_.var(axis=1).nonzero()[0]
    
    @cached_property
    def annotations(self) -> pd.DataFrame:
        return pd.read_csv(ANNOTATIONS_DIR.joinpath(f'{self.name}.csv'),
                           dtype_backend='numpy_nullable')
    
    @cached_property
    def event_bounds(self) -> np.ndarray:
        return _get_event_bounds(self.eventseg_model)
    
    @cached_property
    def events(self) -> np.ndarray:
        return np.load(self.data_dir.joinpath('events.npy'))
    
    @cached_property
    def eventseg_kvals(self) -> np.ndarray:
        return np.load(self.data_dir.joinpath('eventseg_kvals.npy'))
    
    @cached_property
    def eventseg_model(self) -> EventSegment:
        return pickle.loads(self.data_dir.joinpath('eventseg_model.p').read_bytes())

    @cached_property
    def fit_cv(self) -> CountVectorizer:
        return pickle.loads(self.data_dir.joinpath('fit_cv.p').read_bytes())
    
    @cached_property
    def fit_lda(self) -> LatentDirichletAllocation:
        return pickle.loads(self.data_dir.joinpath('fit_lda.p').read_bytes())
    
    @cached_property
    def full_trajectory(self) -> np.ndarray:
        return np.load(self.data_dir.joinpath('full_trajectory.npy'))
    
    @cached_property
    def trajectory(self) -> np.ndarray:
        traj = self.full_trajectory[:, self.active_topics]
        return traj / traj.sum(axis=1, keepdims=True)
        
    @cached_property
    def windows(self) -> list[str]:
        return np.load(self.data_dir.joinpath('windows.npy'))