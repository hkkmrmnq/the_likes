"""remove unique RefreshToken.user_id

Revision ID: bdd19ec56eb8
Revises: 1be83486399d
Create Date: 2026-03-04 12:58:36.645659

"""

from typing import Sequence, Union

from alembic import op

revision: str = 'bdd19ec56eb8'
down_revision: Union[str, Sequence[str], None] = '1be83486399d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint(
        op.f('refreshtokens_user_id_key'), 'refreshtokens', type_='unique'
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.create_unique_constraint(
        op.f('refreshtokens_user_id_key'),
        'refreshtokens',
        ['user_id'],
        postgresql_nulls_not_distinct=False,
    )
