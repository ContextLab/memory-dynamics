<div align="center">
  <h1>🚨&lt;project/repo name placeholder&gt;🚨</h1>
  🚨&lt;preprint/paper badge placeholder&gt;🚨
  <!---
  <a href="🚨<PREPRINT URL>🚨">
    <img src="https://img.shields.io/badge/PsyArXiv-Preprint-cf1d35.svg" alt="PsiArXiv preprint">
  </a>
  --->
</div>

`🚨 indicates content to be updated later`

This repository contains all data and code used to produce the paper
"🚨[_PAPER NAME PLACEHOLDER_](PAPER_URL_PLACEHOLDER)🚨" by 🚨**AUTHORS PLACEHOLDER**🚨.

We also include reproducible environments for running our experiment and
analyses via [Docker](https://www.docker.com/).


## Table of Contents

- [Repository Organization](#repository-organization)
- [Installing Docker](#installing-docker)
  - [Configuring Docker with WSL2 on Windows](#configuring-docker-with-wsl2-on-windows)
- [Running the Analyses](#running-the-analyses)
    - [Option 1: `launch_notebooks.sh`](#option-1-launch_notebookssh)
    - [Option 2: Manual setup](#option-2-manual-setup)
- [Running the Experiment](#running-the-experiment)
- [Other useful documentation](#other-useful-documentation)


## 🚨Repository Organization🚨

🚨update at the end with `tree -dL 2 --gitignore`🚨

The repository is organized as follows:

```yaml
.
├── code : all analysis code used in the paper
│   ├─ notebooks : Jupyter notebooks for running analyses
│   └─ analysis_helpers : Python package with helper code for analyses
├── data : all data analyzed in the paper
│   ├── PLACEHOLDER : PLACEHOLDER TEXT
│   └── PLACEHOLDER : PLACEHOLDER TEXT
├── docker : files for building experiment & analysis environments
├── exp : all code for running the experiment
│   ├── static : scripts, stylesheets, example stimuli, and other static files
│   └── templates : HTML templates for experiment pages
└── paper : LaTeX source files for generating the paper
    ├── CDL-bibliography : submodule for ContextLab BibTeX file
    ├── admin : files related to submission & review process
    └── figs : PDFs of all figures from the paper
```


## Installing Docker

You can install the [Docker Desktop](https://docs.docker.com/desktop/) app for
your operating system using one of the guides below:

- [MacOS](https://docs.docker.com/docker-for-mac/install/)
- [Windows](https://docs.docker.com/docker-for-windows/install/)
- [Debian](https://docs.docker.com/desktop/install/debian/)
- [Fedora](https://docs.docker.com/desktop/install/fedora/)
- [Ubuntu](https://docs.docker.com/desktop/install/ubuntu/)
- [Arch](https://docs.docker.com/desktop/install/archlinux/)

Alternatively, you can install [Docker Engine](https://docs.docker.com/engine/)
(CLI only) for various Linux OSes using one of the guides listed
[here](https://docs.docker.com/engine/install/#server).

**You do not need to create a Docker ID or Docker Hub account to use Docker with
this repo.**

### Configuring Docker with WSL2 on Windows
If you're using Windows, we recommend installing 
[Windows Subsystem for Linux (WSL)](https://learn.microsoft.com/en-us/windows/wsl/about) 
and configuring Docker to use the 
[WSL2 backend](https://docs.docker.com/desktop/windows/wsl/):
1. Open PowerShell as Administrator and run:
   ```powershell
   wsl --install -d Ubuntu
   ```
   You may be prompted to restart your computer. After restarting, an 
   [Ubuntu](https://en.wikipedia.org/wiki/Ubuntu) terminal window should 
   appear automatically. Follow the on-screen prompts to choose a username and 
   password for your Ubuntu account.
2. From the same terminal window, run the following command to install Git 
   inside Ubuntu (if it isn't installed already):
   ```sh
   command -v git > /dev/null 2>&1 || { sudo apt update && sudo apt install -y git; }
   ```
   If prompted for your password, enter the one you just created.
3. Clone the repository to the home directory of your WSL filesystem:
   ```sh
   cd ~ && git clone 🚨https://github.com/ContextLab/memory-dynamics.git🚨
    ```
4. In the Docker Desktop app, go to **Settings → General** and make sure 
   "**Use the WSL 2 based engine**" is selected. Then, go to 
    **Settings → Resources → WSL Integration** and make sure Ubuntu is enabled.

Run the commands in the instructions below from your Ubuntu terminal window.


## Running the Analyses

### Option 1: [`launch_notebooks.sh`](launch_notebooks.sh)

The easiest way to set up and run the analyses is to use the
[`launch_notebooks.sh`](launch_notebooks.sh) script included in this repository.
From the repository root, simply run:

```sh
./launch_notebooks.sh
```

The script will:

1. Start the Docker daemon, if it isn't already running
2. Build the image from [`Dockerfile-analyses`](docker/Dockerfile-analyses), if
   it doesn't already exist
3. Create and run a container from the image, if one doesn't already exist
4. Launch a [Jupyter notebook](https://jupyter.org/) server inside the
   container
5. Open the notebook web app in your default browser
6. Attach stdout to the notebook server logs in the container

The script also accepts a few options to customize behavior:

```console
$ ./launch_notebooks.sh --help

./launch_notebooks.sh [-h] [-d] [-b] [-D] [-i NAME] [-c NAME]

Launch a Jupyter notebook server inside a Docker container for running the
analysis notebooks. The container is set up automatically the first time the
script is run.

Options:
   -h, --help                   Show this help message and exit
   -d, --detach                 Don't attach the terminal to the streaming
                                notebook server log
   -b, --no-browser             Don't try to automatically open notebooks in a
                                browser window
   -D, --dev, --develop         Install helpers package in editable mode when
                                building the image
   -i, --image-name NAME        Run a container from existing image NAME, or
                                build a new image and tag it NAME
   -c, --container-name NAME    Start the existing container NAME, or create a
                                new container named NAME
```

To stop the notebook server and exit the container, press **Control+C**.

The script should work on most systems. If for some reason it doesn't work for
you, or you prefer to manage the environment manually, you can build and run the
analysis environment following the steps below
(and if you encounter any errors, feel free to
🚨[open an issue](https://github.com/ContextLab/memory-dynamics/issues/new)🚨!).

### Option 2: Manual setup

1. Launch the Docker Desktop app or start the Docker daemon from the command 
   line.
2. _From the repository's root directory_, build the "🚨`memory-dynamics`🚨" 
   image from the [Dockerfile-analyses](docker/Dockerfile-analyses) file in the
   [docker](docker) directory:
   ```sh
   docker build --rm -f docker/Dockerfile-analyses -t 🚨memory-dynamics🚨 .
   ```
   (see [Dockerfile-analyses](docker/Dockerfile-analyses) for the various 
   [build arguments](https://docs.docker.com/engine/reference/builder/#arg)
   that can be passed to customize the image)
3. Run a container (named "🚨`MD`🚨") from the newly built image:
   ```sh
   docker run -it -p 8888:8888 --name 🚨MD🚨 -v $PWD:/mnt 🚨memory-dynamics🚨
   ```
   The command above binds port 8888 in the container to port 8888 on the host 
   so the Jupyter notebook server can be accessed from a web browser, and 
   bind-mounts the repository to the container's `/mnt` directory so files in 
   the repo can be accessed and modified from inside it.
4. The notebook server will launch automatically when the container is run. Copy
   and paste the 3rd link that appears (the one starting with
   `http://127.0.0.1:8888`) into a web browser to access the notebook web app.
5. You can then open any notebook in [`code/notebooks/`](code/notebooks) and
   run the code inside it. When finished, return to the terminal and press
   **Control+C** to stop the notebook server and exit the container.
6. To launch the container and notebooks any time after this initial setup, run:
   ```sh
   docker start 🚨MD🚨 && docker attach 🚨MD🚨
   ```


## 🚨Running the Experiment🚨

🚨 **_THIS WHOLE SECTION NEEDS TO BE UPDATED ONCE THE EXPERIMENT CODE IS FINALIZED_** 🚨

1. After [installing Docker](#installing-docker), launch the desktop app or
   start the daemon from the command line.
2. _From the repository's root directory_, build the "`khan-exp`" image from the
   [Dockerfile-experiment](docker/Dockerfile-experiment) file in the
   [docker](docker) directory:

   ```sh
   docker build --rm -f docker/Dockerfile-experiment -t khan-exp .
   ```

3. Run a container (named "`Khan-exp`") from the newly built image:

   ```sh
   docker run -it -p 22363:22363 -v "$PWD/exp:/exp" --name Khan-exp khan-exp
   ```

   The command above bind-mounts the container to the repository's [`exp/`](exp)
   directory so the psiTurk server can read and run the experiment code, and
   binds port 22363 between the container and host so the server can be accessed
   from a web browser.

   **Note**: the port published by the container must match the port listed in
   [`exp/config.txt`](exp/config.txt).

4. Your shell prompt (`$PS1`) should now start with `root@`, indicating that
   you're now running a `bash` shell from _inside_ the container. To start the
   psiTurk experiment server, run:

   ```sh
   psiturk server on
   ```

   When you see "_`Now serving on http://0.0.0.0:22363`_," the experiment server
   is ready. Starting the server for the first time will also create
   `exp/server.log`, a logfile for the experiment server, and
   `exp/efficient-learning-khan.db`, a SQLite database to hold raw experiment
   data.

5. Generate a link to the experiment in "debug mode":

   ```sh
   psiturk debug -p
   ```

   This will output a URL in the format
   `http://0.0.0.0:22363/ad?assignmentId=debug<XXXXXX>&hitId=debug<YYYYYY>&workerId=debug<ZZZZZZ>&mode=debug`,
   where `<XXXXXX>` and `<ZZZZZZ>` will form a unique identifier for the run
   (i.e., a participant's unique ID). In debug mode, the experiment will behave
   normally and data will still be saved properly, but psiTurk will not try to
   connect to [Amazon Mechanical Turk](https://www.mturk.com/)'s servers. This
   is useful because it enables the experiment to be run locally without the
   user having to create AWS & MTurk accounts, supply access keys, etc.

6. Copy and paste the URL into a web browser, and follow the on-screen
   instructions to progress through the experiment. **Note**: the experiment
   will not work in Google Chrome. Recommended browsers include Safari and
   Firefox.

7. When finished, return to the terminal and shut down the experiment server:

   ```sh
   psiturk server off
   ```

   and exit the Docker container by pressing **Control+d** or typing `exit`.

8. To start and enter the container any time after this initial setup, run:

   ```sh
   docker start Khan-exp && docker attach Khan-exp
   ```


## Other useful documentation
- [Docker](https://docs.docker.com/)
    - [`Dockerfile` reference](https://docs.docker.com/engine/reference/builder/)
    - [`docker build` command reference](https://docs.docker.com/engine/reference/commandline/build/)
    - [`docker run` command reference](https://docs.docker.com/engine/reference/run/)
- [Jupyter notebook (v6.4.7)](https://jupyter-notebook.readthedocs.io/en/v6.4.7/)
- [psiTurk](https://psiturk.readthedocs.io/en/stable/)
    - [psiTurk shell commands](https://psiturk.readthedocs.io/en/stable/command_line.html)
    - [Guide to `config.txt` fields](https://psiturk.readthedocs.io/en/stable/settings.html)