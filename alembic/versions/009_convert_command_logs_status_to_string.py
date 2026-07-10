"""009 convert command_logs status to string

Revision ID: 009
Revises: 008_add_planned_routes
Create Date: 2026-07-08

Converts command_logs.status from a PostgreSQL enum type (commandstatus)
to a plain VARCHAR so it can store the full command lifecycle:
  Queued, Delivered, Acknowledged, Executing, Completed, Failed,
  Timed Out, Cancelled
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "009"
down_revision = "008_add_planned_routes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # PostgreSQL: change the column type using USING cast; drop the old enum type.
    # SQLite (dev): ALTER COLUMN is not supported but the column already stores
    # text so no change is needed at the storage level.
    connection = op.get_bind()
    dialect = connection.dialect.name

    if dialect == "postgresql":
        # Step 1: Change column to TEXT, casting via the existing values
        op.execute(
            "ALTER TABLE command_logs "
            "ALTER COLUMN status TYPE VARCHAR "
            "USING status::text"
        )
        # Step 2: Drop the now-unused commandstatus enum type
        # Use IF EXISTS so this is safe to replay
        op.execute("DROP TYPE IF EXISTS commandstatus")
    # SQLite stores everything as TEXT already — no DDL change required.


def downgrade() -> None:
    connection = op.get_bind()
    dialect = connection.dialect.name

    if dialect == "postgresql":
        # Recreate the enum with the original four values
        op.execute(
            "CREATE TYPE commandstatus AS ENUM ('PENDING', 'SENT', 'EXECUTED', 'FAILED')"
        )
        # Cast back — rows with values outside the original enum will fail;
        # truncate or remap if needed before downgrading in production.
        op.execute(
            "ALTER TABLE command_logs "
            "ALTER COLUMN status TYPE commandstatus "
            "USING status::commandstatus"
        )
