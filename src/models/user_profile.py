from typing import TYPE_CHECKING
from uuid import UUID

from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTableUUID
from geoalchemy2 import Geometry
from pydantic import HttpUrl
from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .. import constants as cnst
from ..constants import SUPPORTED_LANGUAGES as sl
from .base import Base, BaseWithIntPK

if TYPE_CHECKING:
    from .contact_n_message import Contact, Message
    from .core import Attitude, ProfileAspectLink
    from .profile_links import ProfileValueLink


class User(SQLAlchemyBaseUserTableUUID, Base):
    __tablename__ = 'users'
    profile: Mapped['User'] = relationship(
        'Profile',
        back_populates='user',
        uselist=False,
        cascade='all, delete-orphan',
    )
    me_contacts: Mapped[list['Contact']] = relationship(
        'Contact',
        back_populates='me_user',
        foreign_keys='Contact.me_user_id',
        cascade='all, delete-orphan',
    )
    in_contacts: Mapped[list['Contact']] = relationship(
        'Contact',
        back_populates='target_user',
        foreign_keys='Contact.target_user_id',
        cascade='all, delete-orphan',
    )
    sent_messages: Mapped[list['Message']] = relationship(
        'Message',
        back_populates='sender',
        foreign_keys='Message.sender_id',
        cascade='all, delete-orphan',
    )
    received_messages: Mapped[list['Message']] = relationship(
        'Message',
        back_populates='receiver',
        foreign_keys='Message.receiver_id',
        cascade='all, delete-orphan',
    )


class Profile(BaseWithIntPK):
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE'), unique=True
    )
    attitude_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey('attitudes.id', ondelete='SET NULL'),
        nullable=True,
    )
    languages: Mapped[list[str]] = mapped_column(
        ARRAY(String), nullable=False, default=['en']
    )
    location: Mapped[str | None] = mapped_column(
        Geometry('POINT', srid=4326), nullable=True, default=None
    )
    distance_limit: Mapped[int] = mapped_column(
        Integer, nullable=True, default=None
    )
    name: Mapped[str | None] = mapped_column(
        String(cnst.USER_NAME_MAX_LENGTH), nullable=True, default=None
    )
    avatar: Mapped[HttpUrl | None] = mapped_column(
        String(cnst.URL_MAX_LENGTH), default=None
    )
    value_links: Mapped[list['ProfileValueLink']] = relationship(
        'ProfileValueLink',
        back_populates='profile',
        cascade='all, delete-orphan',
    )
    attitude: Mapped['Attitude'] = relationship(
        'Attitude', back_populates='profiles'
    )
    user: Mapped['User'] = relationship(
        'User',
        back_populates='profile',
        uselist=False,
    )
    aspect_links: Mapped[list['ProfileAspectLink']] = relationship(
        'ProfileAspectLink',
        back_populates='profile',
        cascade='all, delete-orphan',
    )
    values_agg: Mapped['PVOneLine'] = relationship(
        'PVOneLine',
        back_populates='profile',
        cascade='all, delete-orphan',
    )
    me_contacts: Mapped[list['Contact']] = relationship(
        'Contact',
        foreign_keys='Contact.me_profile_id',
        back_populates='me_profile',
        cascade='all, delete-orphan',
    )
    in_contacts: Mapped[list['Contact']] = relationship(
        'Contact',
        foreign_keys='Contact.target_profile_id',
        back_populates='target_profile',
        cascade='all, delete-orphan',
    )
    sent_messages: Mapped['Message'] = relationship(
        'Message',
        foreign_keys='Message.sender_profile_id',
        back_populates='sender_profile',
        cascade='all, delete-orphan',
    )
    received_messages: Mapped['Message'] = relationship(
        'Message',
        foreign_keys='Message.receiver_profile_id',
        back_populates='receiver_profile',
        cascade='all, delete-orphan',
    )
    __table_args__ = (
        CheckConstraint(
            f'languages <@ ARRAY[{", ".join(f"'{c}'" for c in sl)}]::varchar[]'
        ),
        CheckConstraint('distance_limit > 0'),
        CheckConstraint(f'distance_limit <= {cnst.DISTANCE_MAX_LIMIT}'),
    )


class PVOneLine(BaseWithIntPK):
    profile_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('profiles.id', ondelete='CASCADE'),
        unique=True,
        nullable=False,
    )
    distance_limit: Mapped[int] = mapped_column(
        Integer, nullable=True, default=None
    )
    attitude_id_and_best_uv_ids: Mapped[list[int]] = mapped_column(
        ARRAY(Integer), nullable=False, default=[]
    )
    good_uv_ids: Mapped[list[int]] = mapped_column(
        ARRAY(Integer), nullable=False, default=[]
    )
    neutral_uv_ids: Mapped[list[int]] = mapped_column(
        ARRAY(Integer), nullable=False, default=[]
    )
    bad_uv_ids: Mapped[list[int]] = mapped_column(
        ARRAY(Integer), nullable=False, default=[]
    )
    worst_uv_ids: Mapped[list[int]] = mapped_column(
        ARRAY(Integer), nullable=False, default=[]
    )
    profile: Mapped[Profile] = relationship(
        Profile, back_populates='values_agg'
    )
    __table_args__ = (
        Index(
            'ix_attitude_id_and_best_uv_ids',
            attitude_id_and_best_uv_ids,
            postgresql_using='gin',
        ),
        Index(
            'ix_good_uv_ids',
            good_uv_ids,
            postgresql_using='gin',
        ),
        Index('ix_neutral_uv_ids', neutral_uv_ids, postgresql_using='gin'),
        Index(
            'ix_bad_uv_ids',
            bad_uv_ids,
            postgresql_using='gin',
        ),
        Index(
            'ix_worst_uv_ids',
            worst_uv_ids,
            postgresql_using='gin',
        ),
        CheckConstraint(  # if no positive UVs
            (
                '(cardinality(attitude_id_and_best_uv_ids)'
                f' = {cnst.NUMBER_OF_BEST_UVS + 1})'
                ' OR cardinality(good_uv_ids) = 0'
            ),
            name='check_positive_consistency',
        ),
        CheckConstraint(  # if no negative UVs
            (
                '(cardinality(worst_uv_ids)'
                f' = {cnst.NUMBER_OF_WORST_UVS})'
                ' OR cardinality(bad_uv_ids) = 0'
            ),
            name='check_negative_consistency',
        ),
        CheckConstraint(
            (
                '(cardinality(attitude_id_and_best_uv_ids)'
                ' + cardinality(good_uv_ids)'
                ' + cardinality(neutral_uv_ids)'
                ' + cardinality(bad_uv_ids)'
                ' + cardinality(worst_uv_ids))'
                f' = {cnst.UNIQUE_VALUE_MAX_ORDER + 1}'
            ),
            name='check_total_uvs_number',
        ),
        CheckConstraint(
            (
                'distance_limit IS NULL OR (distance_limit > 0 AND'
                f' distance_limit <= {cnst.DISTANCE_MAX_LIMIT})'
            ),
            name='check_min_max_distance_limit_if_not_null',
        ),
    )
