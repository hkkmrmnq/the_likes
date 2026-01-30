from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from geoalchemy2 import Geography
from sqlalchemy import UUID as SA_UUID
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.config import CNST, ENM

from .base import Base, BaseWithIntPK
from .core import Attitude

if TYPE_CHECKING:
    from .contact_n_message import Contact, Message
    from .personal_values import PersonalAspect, PersonalValue


class User(Base):
    """User DB model."""

    id: Mapped[UUID] = mapped_column(
        SA_UUID(as_uuid=True), primary_key=True, nullable=False, default=uuid4
    )
    email: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=True
    )
    is_verified: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    is_superuser: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
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
    """Profile, 1-to-1-related to User."""

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
    distance_limit: Mapped[float] = mapped_column(
        Float, nullable=True, default=None
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
        CheckConstraint('distance_limit > 0'),
        CheckConstraint(f'distance_limit <= {CNST.DISTANCE_LIMIT_KM_MAX}'),
    )


class UserDynamic(BaseWithIntPK):
    """Utility model to manage user's activity."""

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE'), unique=True, nullable=False
    )
    search_allowed_status: Mapped[str] = mapped_column(
        ENM.SearchAllowedStatusPG
    )
    last_cooldown_start: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    values_created: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), default=None
    )
    values_changes: Mapped[list[datetime]] = mapped_column(
        ARRAY(DateTime(timezone=True)),
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
