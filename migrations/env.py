# migrations/env.py

import logging
from logging.config import fileConfig
from flask import current_app
from alembic import context
import os
import sys

# --- Ensure models are imported ---
sys.path.insert(0, os.path.realpath(os.path.join(os.path.dirname(__file__), '..')))
try:
    import backend.models # Or: from backend import models
    print("INFO: backend.models package imported in env.py")
except ImportError as e:
    print(f"ERROR: Failed to import models: {e}")
    sys.exit(1)
# --- End Model Import ---

# --- Alembic Configuration ---
# ... (rest of env.py remains the same as the previous version) ...
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)
logger = logging.getLogger('alembic.env')

# --- Metadata and Connection Setup ---
if current_app is None:
    print("ERROR: current_app proxy is not active...")
    print("Attempting manual app context push as fallback...")
    try:
        from backend import create_app
        current_app_fallback = create_app()
        if current_app_fallback:
             _context = current_app_fallback.app_context()
             _context.push()
             print("INFO: Manual fallback app context pushed.")
             target_db = current_app_fallback.extensions['migrate'].db
        else:
             print("ERROR: Fallback create_app() failed.")
             sys.exit(1)
    except Exception as e_fallback:
        print(f"ERROR: Fallback app context creation failed: {e_fallback}")
        sys.exit(1)
else:
    target_db = current_app.extensions['migrate'].db

target_metadata = target_db.metadata
logger.info(f"Target Metadata Tables detected: {list(target_metadata.tables.keys())}")

def get_engine():
    try: return target_db.engine
    except AttributeError: return target_db.get_engine()

def get_engine_url():
    try: return get_engine().url.render_as_string(hide_password=False).replace('%', '%%')
    except AttributeError: return str(get_engine().url).replace('%', '%%')

db_url = get_engine_url()
logger.info(f"Setting Alembic sqlalchemy.url to: {db_url.replace('%%', '%')}")
config.set_main_option('sqlalchemy.url', db_url)

# --- Migration Functions ---
def get_metadata():
    return target_metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    is_sqlite = url.startswith('sqlite')
    logger.info(f"Running migrations offline. Batch mode: {is_sqlite}")
    context.configure(url=url, target_metadata=get_metadata(), literal_binds=True, dialect_opts={"paramstyle": "named"}, render_as_batch=is_sqlite)
    with context.begin_transaction(): context.run_migrations()

def run_migrations_online() -> None:
    connectable = get_engine()
    def process_revision_directives(context, revision, directives):
        if getattr(config.cmd_opts, 'autogenerate', False):
            script = directives[0]
            if script.upgrade_ops.is_empty(): directives[:] = []; logger.info('No changes in schema detected.')

    app_for_config = current_app or current_app_fallback
    try: conf_args = app_for_config.extensions['migrate'].configure_args or {}
    except (KeyError, AttributeError): logger.warning("Flask-Migrate extension not found on app context. Using empty configure_args."); conf_args = {}
    if conf_args.get("process_revision_directives") is None: conf_args["process_revision_directives"] = process_revision_directives

    is_sqlite = connectable.driver == 'pysqlite'
    conf_args.pop('render_as_batch', None)
    logger.info(f"Running migrations online. Batch mode {'enabled' if is_sqlite else 'disabled'} for driver: {connectable.driver}")

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=get_metadata(), render_as_batch=is_sqlite, **conf_args)
        with context.begin_transaction(): context.run_migrations()

# --- Main Execution Logic ---
if context.is_offline_mode(): run_migrations_offline()
else: run_migrations_online()

# --- Cleanup Fallback Context if Created ---
if '_context' in locals() and _context: _context.pop(); print("INFO: Fallback app context popped.")
print("INFO: env.py execution finished.")