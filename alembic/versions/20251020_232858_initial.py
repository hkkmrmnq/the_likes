"""Initial

Revision ID: 9ef9208bf451
Revises:
Create Date: 2025-10-20 23:28:58.757324

"""

from typing import Sequence, Union

import geoalchemy2
import sqlalchemy as sa
from fastapi_users_db_sqlalchemy.generics import GUID
from sqlalchemy.dialects import postgresql

from alembic import op
from src.config import constants as CNST
from src.config.enums import ContactStatusPG, PolarityPG, SearchAllowedStatusPG

revision: str = '9ef9208bf451'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        'attitudes',
        sa.Column('statement_default', sa.String(length=500), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('statement_default'),
    )
    op.create_table(
        'users',
        sa.Column('id', GUID(), nullable=False),
        sa.Column('email', sa.String(length=320), nullable=False),
        sa.Column('hashed_password', sa.String(length=1024), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('is_superuser', sa.Boolean(), nullable=False),
        sa.Column('is_verified', sa.Boolean(), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_table(
        'valuetitles',
        sa.Column('name_default', sa.String(length=100), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name_default'),
    )
    op.create_table(
        'attitudetranslations',
        sa.Column('attitude_id', sa.Integer(), nullable=False),
        sa.Column('statement', sa.String(length=500), nullable=False),
        sa.Column('language_code', sa.String(length=2), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['attitude_id'], ['attitudes.id'], ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'contacts',
        sa.Column(
            'my_user_id',
            GUID(),
            nullable=False,
        ),
        sa.Column(
            'other_user_id',
            GUID(),
            nullable=False,
        ),
        sa.Column(
            'status',
            ContactStatusPG,
            nullable=False,
        ),
        sa.Column(
            'created_at',
            sa.DateTime(),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['my_user_id'], ['users.id'], ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['other_user_id'], ['users.id'], ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('my_user_id', 'other_user_id'),
        sa.UniqueConstraint(
            'my_user_id',
            'other_user_id',
            name='unique_contact_my_user_id_other_user_id',
        ),
    )
    op.create_table(
        'messages',
        sa.Column(
            'sender_id',
            GUID(),
            nullable=False,
        ),
        sa.Column(
            'receiver_id',
            GUID(),
            nullable=False,
        ),
        sa.Column('text', sa.String(length=2000), nullable=False),
        sa.Column('is_read', sa.Boolean(), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['receiver_id'], ['users.id'], ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['sender_id'], ['users.id'], ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'profiles',
        sa.Column(
            'user_id',
            GUID(),
            nullable=False,
        ),
        sa.Column('attitude_id', sa.Integer(), nullable=True),
        sa.Column('languages', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column(
            'location',
            geoalchemy2.types.Geography(
                geometry_type='POINT',
                srid=4326,
                dimension=2,
                from_text='ST_GeogFromText',
                name='geography',
            ),
            nullable=True,
        ),
        sa.Column('distance_limit', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=100), nullable=True),
        sa.Column('recommend_me', sa.Boolean(), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.CheckConstraint(CNST.LANGUAGES_CHECK_CONSTRAINT_TEXT),
        sa.CheckConstraint(f'distance_limit <= {CNST.DISTANCE_LIMIT_MAX}'),
        sa.CheckConstraint('distance_limit > 0'),
        sa.ForeignKeyConstraint(
            ['attitude_id'], ['attitudes.id'], ondelete='SET NULL'
        ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
    )
    op.create_table(
        'uniquevalues',
        sa.Column('value_title_id', sa.Integer(), nullable=False),
        sa.Column(
            'aspect_ids', postgresql.ARRAY(sa.Integer()), nullable=False
        ),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['value_title_id'], ['valuetitles.id'], ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(
        'uq_non_empty_aspect_ids',
        'uniquevalues',
        ['aspect_ids'],
        unique=True,
        postgresql_where=sa.text("aspect_ids <> '{}'"),
    )
    op.create_table(
        'userdynamics',
        sa.Column(
            'user_id',
            GUID(),
            nullable=False,
        ),
        sa.Column(
            'search_allowed_status',
            SearchAllowedStatusPG,
            nullable=False,
        ),
        sa.Column('last_cooldown_start', sa.DateTime(), nullable=True),
        sa.Column('values_created', sa.DateTime(), nullable=True),
        sa.Column(
            'values_changes',
            postgresql.ARRAY(sa.DateTime()),
            server_default=sa.text("'{}'"),
            nullable=False,
        ),
        sa.Column('match_notified', sa.Integer(), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.CheckConstraint('match_notified >= 0'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
    )
    op.create_table(
        'valuetitletranslations',
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('value_title_id', sa.Integer(), nullable=False),
        sa.Column('language_code', sa.String(length=2), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['value_title_id'], ['valuetitles.id'], ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'aspects',
        sa.Column('key_phrase_default', sa.String(length=250), nullable=False),
        sa.Column('statement_default', sa.String(length=500), nullable=False),
        sa.Column('value_title_id', sa.Integer(), nullable=False),
        sa.Column('unique_value_id', sa.Integer(), nullable=True),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['unique_value_id'], ['uniquevalues.id'], ondelete='SET NULL'
        ),
        sa.ForeignKeyConstraint(
            ['value_title_id'], ['valuetitles.id'], ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'personalvalues',
        sa.Column(
            'user_id',
            GUID(),
            nullable=False,
        ),
        sa.Column('value_title_id', sa.Integer(), nullable=False),
        sa.Column('unique_value_id', sa.Integer(), nullable=False),
        sa.Column(
            'polarity',
            PolarityPG,
            nullable=False,
        ),
        sa.Column('user_order', sa.Integer(), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.CheckConstraint(
            CNST.PERSONAL_VALUE_MAX_ORDER_CONSTRAINT_TEXT,
            name='max_user_order',
        ),
        sa.CheckConstraint(
            CNST.PERSONAL_VALUE_MIN_ORDER_CONSTRAINT_TEXT,
            name='min_user_order',
        ),
        sa.ForeignKeyConstraint(
            ['unique_value_id'], ['uniquevalues.id'], ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(
            ['value_title_id'], ['valuetitles.id'], ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'user_id', 'value_title_id', name='uq_user_id_value_title_id'
        ),
    )
    op.create_index(
        'unique_personal_value_order',
        'personalvalues',
        ['user_id', 'value_title_id', 'user_order'],
        unique=True,
    )
    op.create_table(
        'aspecttranslations',
        sa.Column('key_phrase', sa.String(length=250), nullable=False),
        sa.Column('statement', sa.String(length=500), nullable=False),
        sa.Column('aspect_id', sa.Integer(), nullable=False),
        sa.Column('language_code', sa.String(length=2), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['aspect_id'], ['aspects.id'], ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'personalaspects',
        sa.Column(
            'user_id',
            GUID(),
            nullable=False,
        ),
        sa.Column('aspect_id', sa.Integer(), nullable=False),
        sa.Column('included', sa.Boolean(), nullable=False),
        sa.Column('personal_value_id', sa.Integer(), nullable=False),
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['aspect_id'], ['aspects.id'], ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['personal_value_id'], ['personalvalues.id'], ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'user_id', 'aspect_id', name='user_aspect_unique_constraint'
        ),
    )
    op.create_table(
        'uniquevalueaspectlinks',
        sa.Column('unique_value_id', sa.Integer(), nullable=False),
        sa.Column('aspect_id', sa.Integer(), nullable=False),
        sa.Column(
            'created_at',
            sa.DateTime(),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(),
            server_default=sa.text('now()'),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ['aspect_id'], ['aspects.id'], ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['unique_value_id'], ['uniquevalues.id'], ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('unique_value_id', 'aspect_id'),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table('uniquevalueaspectlinks')
    op.drop_table('personalaspects')
    op.drop_table('aspecttranslations')
    op.drop_index('unique_personal_value_order', table_name='personalvalues')
    op.drop_table('personalvalues')
    op.drop_table('aspects')
    op.drop_table('valuetitletranslations')
    op.drop_table('userdynamics')
    op.drop_index(
        'uq_non_empty_aspect_ids',
        table_name='uniquevalues',
        postgresql_where=sa.text("aspect_ids <> '{}'"),
    )
    op.drop_table('uniquevalues')
    op.drop_index(
        'idx_profiles_location', table_name='profiles', postgresql_using='gist'
    )
    op.drop_table('profiles')
    op.drop_table('messages')
    op.drop_table('contacts')
    op.drop_table('attitudetranslations')
    op.drop_table('valuetitles')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.drop_table('attitudes')
