from pathlib import Path


BASE_DIR = Path('/dartfs/rc/lab/D/DBIC/CDL/f0028ph/memory-dynamics/')
WORKING_DIR = BASE_DIR / 'scripts'
DATA_DIR = BASE_DIR / 'data'
SCRIPT_DIR = WORKING_DIR / 'job-scripts'
LOCK_DIR = WORKING_DIR / 'locks'
LOG_DIR = WORKING_DIR  / 'logs'

JOB_BASENAME = 'eventseg'
PARTITION = 'standard'
N_NODES = 1
TASKS_PER_NODE = 1
CPUS_PER_TASK = 1
MEMORY = '4G'
WALLTIME = '6:00:00'
CONDA_ENV_NAME = 'memdyn'

MIN_K = 2
MAX_K = 50
N_SPLIT_MERGE_PROPOSALS = 5
N_KVAL_RANGES = 6
