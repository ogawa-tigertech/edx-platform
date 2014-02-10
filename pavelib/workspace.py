"""
Workspace migration tasks.
"""

import os
from paver.easy import *
from .utils.envs import Env


MIGRATION_MARKER_DIR = Env.REPO_ROOT / '.ws_migrations_complete'
MIGRATION_DIR = Env.REPO_ROOT / 'ws_migrations'


@task
def workspace_migrate():
    """
    Run scripts in ws_migrations directory
    """
    if os.getenv('SKIP_WS_MIGRATIONS', False):
        return

    files = os.listdir(MIGRATION_DIR)
    migration_files = []

    for file_handle in files:
        if not file_handle == 'README.rst' and os.access(file_handle, os.X_OK):
            migration_files.append(file_handle)

    for migration in migration_files:
        completion_file = os.path.join(MIGRATION_MARKER_DIR, os.path.basename(migration))
        if not os.path.isfile(completion_file):
            cmd = os.path.join(MIGRATION_DIR, migration)
            sh(cmd)
            open(completion_file, 'w')
