from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from string import Template
from typing import TYPE_CHECKING

import eventseg_config as config

if TYPE_CHECKING:
    from typing import Any


CRUNCHER_SCRIPT = Path(__file__).with_name('eventseg_cruncher.py')
COLLECTOR_SCRIPT = Path(__file__).with_name('eventseg_collector.py')
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
    def __init__(self, name: str, script: Path, args: Any = None) -> None:
        self.name = name
        self.script = script
        self.args = args
        self.scriptfile = config.SCRIPT_DIR.joinpath(f'{name}.sh')
        self.lockfile = config.LOCK_DIR.joinpath(f'{name}.LOCK')
        self.job_command = str(script)
        if args:
            self.job_command = f'{self.job_command} {" ".join(str(arg) for arg in args)}'

    @property
    def is_submitted(self) -> bool:
        return self.lockfile.is_file()

    def submit(self) -> None:
        submit_cmd = f'echo "[SUBMITTING JOB: {self.name}]"; sbatch {self.scriptfile}'
        subprocess.run(submit_cmd, shell=True, check=True)

    def lock(self) -> None:
        self.lockfile.touch()

    def release_lock(self) -> None:
        self.lockfile.unlink(missing_ok=True)

    def write_scriptfile(self) -> None:
        if self.scriptfile.is_file():
            return
        stdout_fpath = config.LOG_DIR / f'{self.name}.out'
        stderr_fpath = config.LOG_DIR / f'{self.name}.err'
        script_contents = JOBSCRIPT_TEMPLATE.substitute(config.__dict__,
                                                        JOB_BASENAME=self.name,
                                                        JOB_COMMAND=self.job_command,
                                                        STDOUT_FPATH=stdout_fpath,
                                                        STDERR_FPATH=stderr_fpath)
        self.scriptfile.write_text(script_contents)


def partition_kval_ranges(
        min_k: int,
        max_k: int,
        n_ranges: int
) -> list[tuple[int, int]]:
    """
    Partition the range [min_k, max_k] into `n_ranges` contiguous
    sub-ranges that should take roughly equal runtime (equal sum(K**2)).
    """
    kvals = list(range(min_k, max_k + 1))
    if len(kvals) < n_ranges:
        raise ValueError(f'cannot split {len(kvals)} K-values into {n_ranges} ranges')

    costs = [k * k for k in kvals]
    total = sum(costs)

    ranges = []
    start = 0
    cumulative = 0
    for range_ix in range(1, n_ranges):
        boundary = total * range_ix / n_ranges
        max_end = len(kvals) - (n_ranges - range_ix) - 1
        end = start
        cumulative_at_end = cumulative + costs[end]
        while (
            end < max_end and
            abs(cumulative_at_end + costs[end + 1] - boundary)
            < abs(cumulative_at_end - boundary)
        ):
            end += 1
            cumulative_at_end += costs[end]
        ranges.append((kvals[start], kvals[end]))
        cumulative = cumulative_at_end
        start = end + 1

    ranges.append((kvals[start], kvals[-1]))
    return ranges


if (
    (EPISODE_DATA_DIR / 'eventseg_kvals.npy').is_file() and
    (EPISODE_DATA_DIR / 'eventseg_model.p').is_file()
):
    print('Collector script outputs already exist; no jobs to submit')
    sys.exit(0)


config.SCRIPT_DIR.mkdir(exist_ok=True)
config.LOCK_DIR.mkdir(exist_ok=True)
config.LOG_DIR.mkdir(exist_ok=True)

kval_ranges = partition_kval_ranges(config.MIN_K, config.MAX_K, config.N_KVAL_RANGES)

jobs = []
for min_k, max_k in kval_ranges:
    job_name = f'eventseg_episode_{min_k}-{max_k}'
    kvals_out = EPISODE_DATA_DIR / f'eventseg_kvals_{min_k}-{max_k}.npy'
    model_out = EPISODE_DATA_DIR / f'eventseg_model_{min_k}-{max_k}.p'
    if not (kvals_out.is_file() and model_out.is_file()):
        job = Job(job_name, CRUNCHER_SCRIPT, (min_k, max_k))
        jobs.append(job)

collector_job = Job('eventseg_collector', COLLECTOR_SCRIPT)
jobs.append(collector_job)

print(f'Submitting {len(jobs)} jobs')

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
