from __future__ import annotations

import pickle
from functools import cached_property
from typing import Literal, TYPE_CHECKING

import numpy as np
import pandas as pd

from analysis_helpers.constants import (
    ANNOTATIONS_DIR,
    ENDFRAME_TIME,
    EPISODE_DATA_DIR
)
from analysis_helpers.internals import Singleton

if TYPE_CHECKING:
    from brainiak.eventseg.event import EventSegment


class Episode(metaclass=Singleton):
    # ADD DOCSTRING
    def __init__(self, name: Literal['atlep1']) -> None:
        if name != 'atlep1':
            raise ValueError(f"Invalid episode name: {name}")
        self.name = name
        self.endframe_time = ENDFRAME_TIME
        self.data_dir = EPISODE_DATA_DIR

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.name!r})'

    @cached_property
    def annotations(self) -> pd.DataFrame:
        return pd.read_csv(ANNOTATIONS_DIR.joinpath(f'{self.name}.csv'),
                           dtype_backend='numpy_nullable')

    @cached_property
    def event_bounds(self) -> np.ndarray:
        labels = self.eventseg_model.segments_[0].argmax(axis=1)
        bounds_aug = np.flatnonzero(np.diff(labels, prepend=-1, append=-1))
        return np.column_stack((bounds_aug[:-1], bounds_aug[1:] - 1))

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
    def trajectory(self) -> np.ndarray:
        return np.load(self.data_dir.joinpath('trajectory.npy'))

    @cached_property
    def windows(self) -> list[str]:
        return np.load(self.data_dir.joinpath('windows.npy'))

    @cached_property
    def path_2d(self) -> np.ndarray:
        return np.load(self.data_dir.joinpath('path_2d.npy'))
