"""Initial

Revision ID: 2f1b871fb490
Revises:
Create Date: 2025-09-23 17:13:08.960530

"""

from typing import Sequence, Union

import geoalchemy2
import sqlalchemy as sa
from fastapi_users_db_sqlalchemy.generics import GUID
from sqlalchemy.dialects import postgresql

from alembic import op
from src.config import constants as CNST

revision: str = '2f1b871fb490'
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
        'profiles',
        sa.Column('user_id', GUID(), nullable=False),
        sa.Column('attitude_id', sa.Integer(), nullable=True),
        sa.Column('languages', postgresql.ARRAY(sa.String()), nullable=False),
        sa.Column(
            'location',
            geoalchemy2.types.Geometry(
                geometry_type='POINT',
                srid=4326,
                dimension=2,
                from_text='ST_GeomFromEWKT',
                name='geometry',
            ),
            nullable=True,
        ),
        sa.Column('distance_limit', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=100), nullable=True),
        sa.Column('avatar', sa.String(length=2048), nullable=True),
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
        sa.CheckConstraint("languages <@ ARRAY['en', 'ru']::varchar[]"),
        sa.CheckConstraint('distance_limit <= 20037509'),
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
        'contacts',
        sa.Column(
            'me_user_id',
            GUID(),
            nullable=False,
        ),
        sa.Column('me_profile_id', sa.Integer(), nullable=False),
        sa.Column(
            'target_user_id',
            GUID(),
            nullable=False,
        ),
        sa.Column('target_profile_id', sa.Integer(), nullable=False),
        sa.Column('similarity_score', sa.Float(), nullable=False),
        sa.Column('distance', sa.Integer(), nullable=True),
        sa.Column('me_ready_to_start', sa.Boolean(), nullable=True),
        sa.Column(
            'status',
            postgresql.ENUM(
                'awaits',
                'rejected',
                'ongoing',
                'closed',
                name='contact_status_enum',
            ),
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
            ['me_profile_id'], ['profiles.id'], ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['me_user_id'], ['users.id'], ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['target_profile_id'], ['profiles.id'], ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['target_user_id'], ['users.id'], ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('me_user_id', 'target_user_id'),
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
        sa.Column('sender_profile_id', sa.Integer(), nullable=False),
        sa.Column('receiver_profile_id', sa.Integer(), nullable=False),
        sa.Column('content', sa.String(length=2000), nullable=False),
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
            ['receiver_profile_id'], ['profiles.id'], ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['sender_id'], ['users.id'], ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['sender_profile_id'], ['profiles.id'], ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_table(
        'profilevaluelinks',
        sa.Column(
            'polarity',
            postgresql.ENUM(
                'positive', 'negative', 'neutral', name='polarity_enum'
            ),
            nullable=False,
        ),
        sa.Column('user_order', sa.Integer(), nullable=False),
        sa.Column('profile_id', sa.Integer(), nullable=False),
        sa.Column('value_title_id', sa.Integer(), nullable=False),
        sa.Column('unique_value_id', sa.Integer(), nullable=False),
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
        sa.CheckConstraint('user_order <= 11', name='max_user_order'),
        sa.CheckConstraint('user_order >= 1', name='min_user_order'),
        sa.ForeignKeyConstraint(
            ['profile_id'], ['profiles.id'], ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['unique_value_id'], ['uniquevalues.id'], ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['value_title_id'], ['valuetitles.id'], ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'profile_id', 'value_title_id', name='profile_value_unique'
        ),
    )
    op.create_index(
        'unique_profile_value_order',
        'profilevaluelinks',
        ['profile_id', 'value_title_id', 'user_order'],
        unique=True,
    )
    op.create_table(
        'pvonelines',
        sa.Column('profile_id', sa.Integer(), nullable=False),
        sa.Column('distance_limit', sa.Integer(), nullable=True),
        sa.Column(
            'attitude_id_and_best_uv_ids',
            postgresql.ARRAY(sa.Integer()),
            nullable=False,
        ),
        sa.Column(
            'good_uv_ids', postgresql.ARRAY(sa.Integer()), nullable=False
        ),
        sa.Column(
            'neutral_uv_ids', postgresql.ARRAY(sa.Integer()), nullable=False
        ),
        sa.Column(
            'bad_uv_ids', postgresql.ARRAY(sa.Integer()), nullable=False
        ),
        sa.Column(
            'worst_uv_ids', postgresql.ARRAY(sa.Integer()), nullable=False
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
        sa.CheckConstraint(
            (
                '('
                'cardinality(attitude_id_and_best_uv_ids) + '
                'cardinality(good_uv_ids) + cardinality(neutral_uv_ids) + '
                'cardinality(bad_uv_ids) + cardinality(worst_uv_ids)'
                ')'
                f' = {CNST.UNIQUE_VALUE_MAX_ORDER + 1}'
            ),
            name='check_total_uvs_number',
        ),
        sa.CheckConstraint(
            (
                '('
                'cardinality(attitude_id_and_best_uv_ids)'
                f' = {CNST.NUMBER_OF_BEST_UVS + 1}'
                ')'
                ' OR '
                '(cardinality(good_uv_ids) = 0)'
            ),
            name='check_positive_consistency',
        ),
        sa.CheckConstraint(
            (
                '('
                'cardinality(worst_uv_ids) = '
                f'{CNST.NUMBER_OF_WORST_UVS}'
                ')'
                ' OR '
                '(cardinality(bad_uv_ids) = 0)'
            ),
            name='check_negative_consistency',
        ),
        sa.CheckConstraint(
            (
                'distance_limit IS NULL OR (distance_limit > 0'
                f' AND distance_limit <= {CNST.DISTANCE_MAX_LIMIT})'
            ),
            name='check_min_max_distance_limit_if_not_null',
        ),
        sa.ForeignKeyConstraint(
            ['profile_id'], ['profiles.id'], ondelete='CASCADE'
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('profile_id'),
    )
    op.create_index(
        'ix_attitude_id_and_best_uv_ids',
        'pvonelines',
        ['attitude_id_and_best_uv_ids'],
        unique=False,
        postgresql_using='gin',
    )
    op.create_index(
        'ix_bad_uv_ids',
        'pvonelines',
        ['bad_uv_ids'],
        unique=False,
        postgresql_using='gin',
    )
    op.create_index(
        'ix_good_uv_ids',
        'pvonelines',
        ['good_uv_ids'],
        unique=False,
        postgresql_using='gin',
    )
    op.create_index(
        'ix_neutral_uv_ids',
        'pvonelines',
        ['neutral_uv_ids'],
        unique=False,
        postgresql_using='gin',
    )
    op.create_index(
        'ix_worst_uv_ids',
        'pvonelines',
        ['worst_uv_ids'],
        unique=False,
        postgresql_using='gin',
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
        'profileaspectlinks',
        sa.Column('included', sa.Boolean(), nullable=False),
        sa.Column('profile_id', sa.Integer(), nullable=False),
        sa.Column('aspect_id', sa.Integer(), nullable=False),
        sa.Column('profile_value_link_id', sa.Integer(), nullable=False),
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
            ['profile_id'], ['profiles.id'], ondelete='CASCADE'
        ),
        sa.ForeignKeyConstraint(
            ['profile_value_link_id'],
            ['profilevaluelinks.id'],
            ondelete='CASCADE',
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint(
            'profile_id', 'aspect_id', name='profile_aspect_unique_constraint'
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
    op.drop_table('profileaspectlinks')
    op.drop_table('aspecttranslations')
    op.drop_index(
        'ix_worst_uv_ids', table_name='pvonelines', postgresql_using='gin'
    )
    op.drop_index(
        'ix_neutral_uv_ids', table_name='pvonelines', postgresql_using='gin'
    )
    op.drop_index(
        'ix_good_uv_ids', table_name='pvonelines', postgresql_using='gin'
    )
    op.drop_index(
        'ix_bad_uv_ids', table_name='pvonelines', postgresql_using='gin'
    )
    op.drop_index(
        'ix_attitude_id_and_best_uv_ids',
        table_name='pvonelines',
        postgresql_using='gin',
    )
    op.drop_table('pvonelines')
    op.drop_index('unique_profile_value_order', table_name='profilevaluelinks')
    op.drop_table('profilevaluelinks')
    op.drop_table('messages')
    op.drop_table('contacts')
    op.drop_table('aspects')
    op.drop_table('valuetitletranslations')
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
    op.drop_table('attitudetranslations')
    op.drop_table('valuetitles')
    op.drop_index(op.f('ix_users_email'), table_name='users')
    op.drop_table('users')
    op.drop_table('attitudes')
