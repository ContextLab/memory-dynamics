from importlib import metadata

from analysis_helpers.episode import Episode
from analysis_helpers.participant import Participant
from analysis_helpers.functions import set_figure_style, show_content_warning


__version__ = metadata.version("analysis-helpers")

set_figure_style()