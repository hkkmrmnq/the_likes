"""Message cascade delete

Revision ID: ef9874a0a3fc
Revises: 4b5312105509
Create Date: 2025-09-20 11:45:58.054449

"""

from typing import Sequence, Union

from alembic import op

revision: str = 'ef9874a0a3fc'
down_revision: Union[str, Sequence[str], None] = '4b5312105509'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint(
        op.f('messages_receiver_id_fkey'), 'messages', type_='foreignkey'
    )
    op.drop_constraint(
        op.f('messages_receiver_profile_id_fkey'),
        'messages',
        type_='foreignkey',
    )
    op.drop_constraint(
        op.f('messages_sender_id_fkey'), 'messages', type_='foreignkey'
    )
    op.drop_constraint(
        op.f('messages_sender_profile_id_fkey'), 'messages', type_='foreignkey'
    )
    op.create_foreign_key(
        'sender_id_fk',
        'messages',
        'users',
        ['sender_id'],
        ['id'],
        ondelete='CASCADE',
    )
    op.create_foreign_key(
        'receiver_profile_id_fk',
        'messages',
        'profiles',
        ['receiver_profile_id'],
        ['id'],
        ondelete='CASCADE',
    )
    op.create_foreign_key(
        'sender_profile_id_fk',
        'messages',
        'profiles',
        ['sender_profile_id'],
        ['id'],
        ondelete='CASCADE',
    )
    op.create_foreign_key(
        'receiver_id_fk',
        'messages',
        'users',
        ['receiver_id'],
        ['id'],
        ondelete='CASCADE',
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint('sender_id_fk', 'messages', type_='foreignkey')
    op.drop_constraint(
        'receiver_profile_id_fk', 'messages', type_='foreignkey'
    )
    op.drop_constraint('sender_profile_id_fk', 'messages', type_='foreignkey')
    op.drop_constraint('receiver_id_fk', 'messages', type_='foreignkey')
    op.create_foreign_key(
        op.f('messages_sender_profile_id_fkey'),
        'messages',
        'profiles',
        ['sender_profile_id'],
        ['id'],
        ondelete='SET NULL',
    )
    op.create_foreign_key(
        op.f('messages_sender_id_fkey'),
        'messages',
        'users',
        ['sender_id'],
        ['id'],
        ondelete='SET NULL',
    )
    op.create_foreign_key(
        op.f('messages_receiver_profile_id_fkey'),
        'messages',
        'profiles',
        ['receiver_profile_id'],
        ['id'],
        ondelete='SET NULL',
    )
    op.create_foreign_key(
        op.f('messages_receiver_id_fkey'),
        'messages',
        'users',
        ['receiver_id'],
        ['id'],
        ondelete='SET NULL',
    )
