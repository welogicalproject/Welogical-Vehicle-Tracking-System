import logging
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine
from alembic.config import Config
from alembic import script

logger = logging.getLogger("app.migrations")

async def verify_migrations_are_current(engine: AsyncEngine):
    """
    Verify that the database schema is fully up to date with Alembic migration HEAD.
    Raises RuntimeError if there is a mismatch.
    """
    try:
        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT version_num FROM alembic_version LIMIT 1"))
            row = result.fetchone()
            db_version = row[0] if row else None
    except Exception as e:
        logger.warning(f"Could not read alembic_version table: {e}")
        db_version = None

    try:
        alembic_cfg = Config("alembic.ini")
        script_dir = script.ScriptDirectory.from_config(alembic_cfg)
        head_revision = script_dir.get_current_head()
    except Exception as e:
        logger.error(f"Failed to load Alembic config: {e}")
        return

    if db_version != head_revision:
        raise RuntimeError(
            f"Database migration drift detected! "
            f"Database version: {db_version}, Migration HEAD: {head_revision}. "
            f"Please run 'alembic upgrade head' to synchronize the database schema."
        )
    logger.info(f"Database migration check passed: HEAD is {head_revision}")
