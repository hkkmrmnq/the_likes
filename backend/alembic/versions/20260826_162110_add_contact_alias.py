"""Add Contact alias

Revision ID: 006ae07dca08
Revises: bdd19ec56eb8
Create Date: 2026-08-26 16:21:10.264491

"""

from typing import Sequence, Union

import sqlalchemy as sa

from alembic import op

revision: str = '006ae07dca08'
down_revision: Union[str, Sequence[str], None] = 'bdd19ec56eb8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'contacts', sa.Column('alias', sa.String(length=100), nullable=True)
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('contacts', 'alias')
