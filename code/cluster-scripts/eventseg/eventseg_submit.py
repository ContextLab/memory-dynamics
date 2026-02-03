import subprocess
from pathlib import Path
from string import Template

import eventseg_config as config

job_names = []
job_args = []

CRUNCHER_SCRIPT = Path(__file__).with_name('eventseg_cruncher.py')

########################################################################
PARTICIPANTS_DIR = config.DATA_DIR.joinpath('participants')
MIN_K = 2
MAX_K = 50
N_SPLIT_MERGE_PROPOSALS = 3

for participant_dir in PARTICIPANTS_DIR.glob('MD-*'):
    for rectype in ('atlep1', 'delayed'):
        if (
            participant_dir.joinpath(f'{rectype}_recall_eventseg_kvals.npy').is_file() and
            participant_dir.joinpath(f'{rectype}_recall_eventseg_model.p').is_file()
        ):
            continue
        job_names.append(f'eventseg_{participant_dir.name}_{rectype}')
        job_args.append((participant_dir.name, rectype, MIN_K, MAX_K, N_SPLIT_MERGE_PROPOSALS))
#######################################################################

if len(job_args) != len(job_names):
    raise ValueError('job_commands and job_names must be the same length')

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
    def __init__(self, name, args):
        self.name = name
        self.args = args
        self.scriptfile = config.SCRIPT_DIR.joinpath(f'{name}.sh')
        self.lockfile = config.LOCK_DIR.joinpath(f'{name}.LOCK')
        self.job_command = f'{CRUNCHER_SCRIPT} {" ".join(str(arg) for arg in self.args)}'

    @property
    def is_submitted(self):
        return self.lockfile.is_file()

    def submit(self):
        submit_cmd = f'echo "[SUBMITTING JOB: {self.name}]"; sbatch {self.scriptfile}'
        subprocess.run(submit_cmd, shell=True, check=True)

    def lock(self):
        self.lockfile.touch()

    def release_lock(self):
        self.lockfile.unlink()

    def write_scriptfile(self):
        if self.scriptfile.is_file():
            return
        stdout_fpath = config.LOG_DIR.joinpath(f'{self.name}.out')
        stderr_fpath = config.LOG_DIR.joinpath(f'{self.name}.err')
        script_contents = JOBSCRIPT_TEMPLATE.substitute(config.__dict__,
                                                        JOB_COMMAND=self.job_command,
                                                        STDOUT_FPATH=stdout_fpath,
                                                        STDERR_FPATH=stderr_fpath)
        self.scriptfile.write_text(script_contents)


config.SCRIPT_DIR.mkdir(exist_ok=True)
config.LOCK_DIR.mkdir(exist_ok=True)
config.LOG_DIR.mkdir(exist_ok=True)

jobs = []

for job_n, job_a in zip(job_names, job_args):
    job = Job(job_n, job_a)
    if not job.is_submitted:
        job.write_scriptfile()
        job.submit()
        job.lock()
    jobs.append(job)

for job in jobs:
    job.release_lock()
config.LOCK_DIR.rmdir()
