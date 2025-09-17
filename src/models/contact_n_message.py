from typing import TYPE_CHECKING

from fastapi_users_db_sqlalchemy import UUID_ID
from sqlalchemy import (
    Boolean,
    Float,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .. import constants as cnst
from .base import Base, BaseWithIntPK

if TYPE_CHECKING:
    from .user_profile import Profile, User


class Contact(Base):
    me_user_id: Mapped[UUID_ID] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE'), primary_key=True
    )
    me_profile_id: Mapped[int] = mapped_column(
        ForeignKey('profiles.id', ondelete='CASCADE')
    )
    target_user_id: Mapped[UUID_ID] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE'), primary_key=True
    )
    target_profile_id: Mapped[int] = mapped_column(
        ForeignKey('profiles.id', ondelete='CASCADE')
    )
    similarity_score: Mapped[float] = mapped_column(Float)
    distance: Mapped[int | None] = mapped_column(
        Integer, nullable=True, default=None
    )
    me_ready_to_start: Mapped[bool] = mapped_column(
        Boolean, nullable=True, default=False
    )
    status: Mapped[str] = mapped_column(cnst.ContactStatusEnum)
    me_user: Mapped['User'] = relationship(
        'User',
        foreign_keys=[me_user_id],
        back_populates='me_contacts',
        uselist=False,
    )
    target_user: Mapped['User'] = relationship(
        'User', foreign_keys=[target_user_id], uselist=False
    )
    me_profile: Mapped['Profile'] = relationship(
        'Profile',
        foreign_keys=[me_profile_id],
        back_populates='me_contacts',
        uselist=False,
    )
    target_profile: Mapped['Profile'] = relationship(
        'Profile', foreign_keys=[target_profile_id], uselist=False
    )


class Message(BaseWithIntPK):
    sender_id: Mapped[UUID_ID] = mapped_column(
        ForeignKey('users.id', ondelete='SET NULL')
    )
    receiver_id: Mapped[UUID_ID] = mapped_column(
        ForeignKey('users.id', ondelete='SET NULL')
    )
    sender_profile_id: Mapped[int] = mapped_column(
        ForeignKey('profiles.id', ondelete='SET NULL')
    )
    receiver_profile_id: Mapped[int] = mapped_column(
        ForeignKey('profiles.id', ondelete='SET NULL')
    )
    content: Mapped[str] = mapped_column(
        String(cnst.MESSAGE_MAX_LENGTH), nullable=False
    )
    is_read: Mapped[bool] = mapped_column(default=False, nullable=False)
    sender: Mapped['User'] = relationship(
        'User',
        foreign_keys=[sender_id],
        back_populates='sent_messages',
        uselist=False,
    )
    receiver: Mapped['User'] = relationship(
        'User',
        foreign_keys=[receiver_id],
        back_populates='received_messages',
        uselist=False,
    )
    sender_profile: Mapped['Profile'] = relationship(
        'Profile',
        foreign_keys=[sender_profile_id],
        back_populates='sent_messages',
        uselist=False,
    )
    receiver_profile: Mapped['Profile'] = relationship(
        'Profile',
        foreign_keys=[receiver_profile_id],
        back_populates='received_messages',
        uselist=False,
    )
