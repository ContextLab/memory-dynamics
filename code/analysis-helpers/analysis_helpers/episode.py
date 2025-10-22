from __future__ import annotations

import pickle
from functools import cached_property
from typing import Literal

import numpy as np
import pandas as pd
from sklearn.decomposition import LatentDirichletAllocation
from sklearn.feature_extraction.text import CountVectorizer

from analysis_helpers.constants import (
    ANNOTATIONS_DIR, 
    ENDFRAME_TIMES,
    EPISODE_DATA_DIR
)
from analysis_helpers.internals import Multiton


class Episode(metaclass=Multiton):
    # ADD DOCSTRING
    def __init__(self, name: Literal['atlep1', 'atlep2', 'arrdev']) -> None:
        if name not in {'atlep1', 'atlep2', 'arrdev'}:
            raise ValueError(f"Invalid episode name: {name}")
        self.name = name
        self.endframe_time = ENDFRAME_TIMES[name]
        self.data_dir = EPISODE_DATA_DIR.joinpath(name)

    @cached_property
    def annotations(self) -> pd.DataFrame:
        return pd.read_csv(ANNOTATIONS_DIR.joinpath(f'{self.name}.csv'),
                           dtype_backend='numpy_nullable')

    @cached_property
    def fit_cv(self) -> CountVectorizer:
        return pickle.loads(self.data_dir.joinpath('fit_cv.p').read_bytes())
    
    @cached_property
    def fit_lda(self) -> LatentDirichletAllocation:
        return pickle.loads(self.data_dir.joinpath('fit_lda.p').read_bytes())
    
    @cached_property
    def trajectory(self) -> np.ndarray:
        return np.load(self.data_dir.joinpath('trajectory.npy'))

    @cached_property
    def windows(self) -> list[str]:
        return np.load(self.data_dir.joinpath('windows.npy'))