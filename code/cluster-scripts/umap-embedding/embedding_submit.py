import subprocess
import sys
from collections.abc import Iterable
from pathlib import Path
from string import Template

import embedding_config as config


try:
    MODE = sys.argv[1]
    if MODE not in ('cruncher', 'collector'):
        raise ValueError(f'invalid argument, {MODE}')
except IndexError:
    MODE = 'cruncher'

CRUNCHER_SCRIPT = Path(__file__).with_name('embedding_cruncher.py')
COLLECTOR_SCRIPT = Path(__file__).with_name('embedding_collector.py')
EPISODE_DATA_DIR = config.DATA_DIR.joinpath('episodes', 'atlep1')

JOBSCRIPT_TEMPLATE = Template("""\
#!/bin/bash -l

#SBATCH --job-name=$JOB_BASENAME
#SBATCH --partition=$PARTITION
#SBATCH --nodes=$N_NODES
#SBATCH --ntasks-per-node=$TASKS_PER_NODE
#SBATCH --cpus-per-task=$CPUS_PER_TASK
#SBATCH --mem=$MEMORY
#SBATCH --time=$WALLTIME
#SBATCH --output=$STDOUT_FPATH
#SBATCH --error=$STDERR_FPATH
#SBATCH --chdir=$WORKING_DIR

echo "activating conda environment: $CONDA_ENV_NAME"
conda activate $CONDA_ENV_NAME
echo "running job script with args: $JOB_COMMAND"
python $JOB_COMMAND
""")


class Job:
    def __init__(self, name, script, args=()):
        self.name = name
        self.script = script
        if not isinstance(args, Iterable) or isinstance(args, str):
            self.args = (args,)
        else:
            self.args = tuple(args)
        self.scriptfile = config.SCRIPT_DIR.joinpath(f'{name}.sh')
        self.lockfile = config.LOCK_DIR.joinpath(f'{name}.LOCK')
        self.job_command = str(script)
        if self.args:
            self.job_command = f'{self.job_command} {" ".join(str(arg) for arg in self.args)}'

    @property
    def is_submitted(self):
        return self.lockfile.is_file()

    def submit(self):
        submit_cmd = f'echo "[SUBMITTING JOB: {self.name}]"; sbatch {self.scriptfile}'
        subprocess.run(submit_cmd, shell=True, check=True)

    def lock(self):
        self.lockfile.touch()

    def release_lock(self):
        self.lockfile.unlink(missing_ok=True)

    def write_scriptfile(self):
        if self.scriptfile.is_file():
            return
        stdout_fpath = config.LOG_DIR.joinpath(f'{self.name}.out')
        stderr_fpath = config.LOG_DIR.joinpath(f'{self.name}.err')
        script_contents = JOBSCRIPT_TEMPLATE.substitute(config.__dict__,
                                                        JOB_BASENAME=self.name,
                                                        JOB_COMMAND=self.job_command,
                                                        STDOUT_FPATH=stdout_fpath,
                                                        STDERR_FPATH=stderr_fpath)
        self.scriptfile.write_text(script_contents)


config.SCRIPT_DIR.mkdir(exist_ok=True)
config.LOCK_DIR.mkdir(exist_ok=True)
config.LOG_DIR.mkdir(exist_ok=True)

jobs = []
if MODE == 'cruncher':
    for seed in range(*config.RANDOM_STATE_RANGE):
        for center_strat in config.CENTERING_STRATEGIES:
            job = Job(f'embedding_seed{seed}_center{center_strat}', CRUNCHER_SCRIPT, (seed, center_strat))
            jobs.append(job)
else:
    for center_strat in config.CENTERING_STRATEGIES:
        job = Job(f'embedding_collector_center{center_strat}', COLLECTOR_SCRIPT, center_strat)
        jobs.append(job)

print(f'Submitting {len(jobs)} {MODE} jobs')

for job in jobs:
    if not job.is_submitted:
        job.write_scriptfile()
        job.submit()
        job.lock()

for job in jobs:
    job.release_lock()
try:
    config.LOCK_DIR.rmdir()
except OSError:
    pass
