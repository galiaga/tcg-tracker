# migrations/env.py

import logging
from logging.config import fileConfig

from flask import current_app

from alembic import context

# Existing config setup...
config = context.config
fileConfig(config.config_file_name)
logger = logging.getLogger('alembic.env')

# Existing helper functions...
def get_engine():
    try:
        # Use the engine directly if available
        return current_app.extensions['migrate'].db.engine
    except AttributeError:
        # Fallback for older Flask-SQLAlchemy versions or different setups
        return current_app.extensions['migrate'].db.get_engine()

def get_engine_url():
    try:
        return get_engine().url.render_as_string(hide_password=False).replace(
            '%', '%%')
    except AttributeError:
        return str(get_engine().url).replace('%', '%%')

config.set_main_option('sqlalchemy.url', get_engine_url())
target_db = current_app.extensions['migrate'].db

def get_metadata():
    if hasattr(target_db, 'metadatas'):
        return target_db.metadatas[None]
    return target_db.metadata

# --- run_migrations_offline ---
def run_migrations_offline():
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    # --- Add batch mode check for SQLite based on URL ---
    is_sqlite = url.startswith('sqlite')
    context.configure(
        url=url,
        target_metadata=get_metadata(),
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # Add this line:
        render_as_batch=is_sqlite
    )
    # --- End of change ---

    with context.begin_transaction():
        context.run_migrations()

# --- run_migrations_online ---
def run_migrations_online():
    """Run migrations in 'online' mode."""

    def process_revision_directives(context, revision, directives):
        if getattr(config.cmd_opts, 'autogenerate', False):
            script = directives[0]
            if script.upgrade_ops.is_empty():
                directives[:] = []
                logger.info('No changes in schema detected.')

    # Ensure configure_args is initialized if not present
    conf_args = current_app.extensions['migrate'].configure_args or {}
    if conf_args.get("process_revision_directives") is None:
        conf_args["process_revision_directives"] = process_revision_directives

    conf_args.pop('render_as_batch', None)
    
    connectable = get_engine()

    # --- Add batch mode check for SQLite based on engine driver ---
    # Check the driver of the engine
    is_sqlite = connectable.driver == 'pysqlite'
    # Add the render_as_batch key to the conf_args dictionary
    conf_args['render_as_batch'] = is_sqlite
    logger.info(f"Batch mode {'enabled' if is_sqlite else 'disabled'} for driver: {connectable.driver}")
    # --- End of change ---

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=get_metadata(),
            **conf_args # Pass the modified conf_args including render_as_batch
        )

        with context.begin_transaction():
            # Pass the migration context if needed by your setup, otherwise default is fine
            context.run_migrations() # You can pass context=context if needed


# --- Main execution logic ---
if context.is_offline_mode():
    logger.info("Running migrations in offline mode...")
    run_migrations_offline()
else:
    logger.info("Running migrations in online mode...")
    run_migrations_online()