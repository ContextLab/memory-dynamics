"""
Config file for the Jupyter notebook server.

Sets some options for serving notebooks from inside a Docker container
based on arguments passed during build.
"""
from os import getenv


# server config options
c.ServerApp.ip = getenv("NOTEBOOK_IP")
c.ServerApp.port = int(getenv("NOTEBOOK_PORT"))
c.ServerApp.root_dir = getenv("NOTEBOOK_DIR")
c.ServerApp.open_browser = False
c.ServerApp.allow_root = True

# notebook app config options
c.Completer.use_jedi = False
c.IPCompleter.use_jedi = False
c.NotebookApp.show_banner = False
# https://github.com/jupyter/notebook/issues/3130
c.FileContentsManager.delete_to_trash = False