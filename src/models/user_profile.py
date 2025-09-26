from typing import TYPE_CHECKING
from uuid import UUID

from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTableUUID
from geoalchemy2 import Geometry
from pydantic import HttpUrl
from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..config import constants as CNST
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
        String(CNST.USER_NAME_MAX_LENGTH), nullable=True, default=None
    )
    avatar: Mapped[HttpUrl | None] = mapped_column(
        String(CNST.URL_MAX_LENGTH), default=None
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
        CheckConstraint(CNST.LANGUAGES_CHECK_CONSTRAINT_TEXT),
        CheckConstraint('distance_limit > 0'),
        CheckConstraint(f'distance_limit <= {CNST.DISTANCE_LIMIT_MAX}'),
    )
