from pathlib import Path


BASE_DIR = Path('/dartfs/rc/lab/D/DBIC/CDL/f0028ph/memory-dynamics/')
WORKING_DIR = BASE_DIR.joinpath('scripts')
DATA_DIR = BASE_DIR.joinpath('data')
SCRIPT_DIR = WORKING_DIR.joinpath('job-scripts')
LOCK_DIR = WORKING_DIR.joinpath('locks')
LOG_DIR = WORKING_DIR.joinpath('logs')

JOB_BASENAME = 'eventseg'
PARTITION = 'standard'
N_NODES = 1
TASKS_PER_NODE = 1
CPUS_PER_TASK = 1
MEMORY = '4G'
WALLTIME = '1:20:00'
CONDA_ENV_NAME = 'memdyn'
