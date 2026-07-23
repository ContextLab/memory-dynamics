from pathlib import Path


BASE_DIR = Path('/dartfs/rc/lab/D/DBIC/CDL/f0028ph/memory-dynamics/')
WORKING_DIR = BASE_DIR.joinpath('scripts')
DATA_DIR = BASE_DIR.joinpath('data')
SCRIPT_DIR = WORKING_DIR.joinpath('job-scripts')
LOCK_DIR = WORKING_DIR.joinpath('locks')
LOG_DIR = WORKING_DIR.joinpath('logs')

JOB_BASENAME = 'embedding'
PARTITION = 'standard'
N_NODES = 1
TASKS_PER_NODE = 1
CPUS_PER_TASK = 1
MEMORY = '2G'
WALLTIME = '6:00:00'
CONDA_ENV_NAME = 'memdyn'

RANDOM_STATE_RANGE = (0, 100)
N_NEIGHBORS_VALS = (10, 15, 30, 50, 75) + tuple(range(100, 501, 50))
MIN_DIST_ARANGE = (0.1, 1, 0.2)
SPREAD_RANGE = (1, 10, 2)
# CENTERING STRATEGIES:
#   - 0: no centering
#   - 1: each recall centered individually
#   - 2: each participant's immediate + delayed recall centered jointly
#   - 3: all recalls centered together
CENTERING_STRATEGIES = (0, 1, 2, 3)