import subprocess
import sys
from pathlib import Path
from string import Template

import eventseg_config as config


MODE = sys.argv[1]

job_names = []
job_args = []

if MODE == 'episode':
    CRUNCHER_SCRIPT = Path(__file__).with_name('eventseg_cruncher_episode.py')
    EPISODE_DATA_DIR = config.DATA_DIR.joinpath('episodes', 'atlep1')
    if not (
        EPISODE_DATA_DIR.joinpath('eventseg_kvals.npy').is_file() and
        EPISODE_DATA_DIR.joinpath('eventseg_model.p').is_file()
    ):
        job_names.append('eventseg_episode')
        job_args.append(())

elif MODE == 'participant':
    CRUNCHER_SCRIPT = Path(__file__).with_name('eventseg_cruncher_participant.py')
    PARTICIPANTS_DIR = config.DATA_DIR.joinpath('participants')
    for participant_dir in PARTICIPANTS_DIR.glob('MD-*'):
        for rectype in ('atlep1', 'delayed'):
            if (
                participant_dir.joinpath(f'{rectype}_recall_eventseg_kvals.npy').is_file() and
                participant_dir.joinpath(f'{rectype}_recall_eventseg_model.p').is_file()
            ):
                continue

            if not config.LOG_DIR.joinpath(f'eventseg_{participant_dir.name}_{rectype}.out').is_file():
                job_names.append(f'eventseg_{participant_dir.name}_{rectype}')
                job_args.append((participant_dir.name, rectype))

else:
    raise ValueError(f'Invalid mode: "{MODE}", must be "episode" or "participant"')

if len(job_args) != len(job_names):
    raise ValueError('job_commands and job_names must be the same length')
elif len(job_names) == 0:
    print('No jobs to submit')
    sys.exit(0)
else:
    print(f'Submitting {len(job_names)} jobs')


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
        self.job_command = str(CRUNCHER_SCRIPT)
        if args:
            self.job_command = f'{self.job_command} {" ".join(str(arg) for arg in args)}'

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
