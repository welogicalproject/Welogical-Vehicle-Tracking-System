"""Alter tables to use timezone-aware datetime columns

Revision ID: 002_timezone_aware
Revises: 001_initial_migration
Create Date: 2026-06-23 12:40:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "002_timezone_aware"
down_revision: Union[str, None] = "001_initial_migration"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Alter vehicles table columns to timezone-naive
    op.alter_column(
        "vehicles",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime(timezone=False),
        existing_nullable=False
    )
    op.alter_column(
        "vehicles",
        "last_seen",
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime(timezone=False),
        existing_nullable=True
    )
    
    # Alter locations table columns to timezone-naive
    op.alter_column(
        "locations",
        "timestamp",
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime(timezone=False),
        existing_nullable=False
    )

    # Alter raw_packets table columns to timezone-naive
    op.alter_column(
        "raw_packets",
        "created_at",
        existing_type=sa.DateTime(timezone=True),
        type_=sa.DateTime(timezone=False),
        existing_nullable=False
    )


def downgrade() -> None:
    # Keep raw_packets table columns timezone-naive
    op.alter_column(
        "raw_packets",
        "created_at",
        existing_type=sa.DateTime(timezone=False),
        type_=sa.DateTime(timezone=False),
        existing_nullable=False
    )

    # Keep locations table columns timezone-naive
    op.alter_column(
        "locations",
        "timestamp",
        existing_type=sa.DateTime(timezone=False),
        type_=sa.DateTime(timezone=False),
        existing_nullable=False
    )

    # Keep vehicles table columns timezone-naive
    op.alter_column(
        "vehicles",
        "last_seen",
        existing_type=sa.DateTime(timezone=False),
        type_=sa.DateTime(timezone=False),
        existing_nullable=True
    )
    op.alter_column(
        "vehicles",
        "created_at",
        existing_type=sa.DateTime(timezone=False),
        type_=sa.DateTime(timezone=False),
        existing_nullable=False
    )
