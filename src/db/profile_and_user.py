from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

from fastapi_users_db_sqlalchemy import SQLAlchemyBaseUserTableUUID
from geoalchemy2 import Geography
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.config import constants as CNST
from src.config.enums import SearchAllowedStatusPG
from src.db.base import Base, BaseWithIntPK
from src.db.core import Attitude

if TYPE_CHECKING:
    from .contact_n_message import Contact, Message
    from .personal_values import PersonalAspect, PersonalValue


class User(SQLAlchemyBaseUserTableUUID, Base):
    __tablename__ = 'users'
    profile: Mapped['Profile'] = relationship(
        'Profile',
        back_populates='user',
        uselist=False,
        cascade='all, delete-orphan',
    )
    my_contacts: Mapped[list['Contact']] = relationship(
        'Contact',
        back_populates='my_user',
        foreign_keys='Contact.my_user_id',
        cascade='all, delete-orphan',
    )
    in_contacts: Mapped[list['Contact']] = relationship(
        'Contact',
        back_populates='other_user',
        foreign_keys='Contact.other_user_id',
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
    dynamic: Mapped['UserDynamic'] = relationship(
        'UserDynamic',
        back_populates='user',
        cascade='all, delete-orphan',
        uselist=False,
    )
    personal_values: Mapped[list['PersonalValue']] = relationship(
        'PersonalValue',
        back_populates='user',
        cascade='all, delete-orphan',
    )
    personal_aspects: Mapped[list['PersonalAspect']] = relationship(
        'PersonalAspect',
        back_populates='user',
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
        ARRAY(String), nullable=False, default=lambda: ['en']
    )
    location: Mapped[str | None] = mapped_column(
        Geography('POINT', srid=4326), nullable=True, default=None, index=True
    )
    distance_limit: Mapped[int] = mapped_column(
        Integer, nullable=True, default=None
    )
    name: Mapped[str | None] = mapped_column(
        String(CNST.USER_NAME_MAX_LENGTH), nullable=True, default=None
    )
    recommend_me: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )
    attitude: Mapped['Attitude'] = relationship(
        'Attitude', back_populates='profiles'
    )
    user: Mapped['User'] = relationship(
        'User',
        back_populates='profile',
        uselist=False,
    )

    __table_args__ = (
        CheckConstraint(CNST.LANGUAGES_CHECK_CONSTRAINT_TEXT),
        CheckConstraint('distance_limit > 0'),
        CheckConstraint(f'distance_limit <= {CNST.DISTANCE_LIMIT_MAX}'),
    )


class UserDynamic(BaseWithIntPK):
    user_id: Mapped[UUID] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False
    )
    search_allowed_status: Mapped[str] = mapped_column(SearchAllowedStatusPG)
    last_cooldown_start: Mapped[datetime | None] = mapped_column(default=None)
    values_created: Mapped[datetime | None] = mapped_column(default=None)
    values_changes: Mapped[list[datetime]] = mapped_column(
        ARRAY(DateTime(timezone=False)),
        default=list,
    )
    match_notified: Mapped[int] = mapped_column(
        Integer, nullable=False, default=0
    )
    user: Mapped[User] = relationship(
        User,
        back_populates='dynamic',
        uselist=False,
    )
    __table_args__ = (CheckConstraint('match_notified >= 0'),)
