from fastapi_users_db_sqlalchemy import UUID_ID
from sqlalchemy import ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.config import constants as CNST
from src.config.enums import ContactStatus, ContactStatusPG
from src.db.base import Base, BaseWithIntPK
from src.db.user_and_profile import User


class Contact(Base):
    my_user_id: Mapped[UUID_ID] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE'), primary_key=True
    )
    other_user_id: Mapped[UUID_ID] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE'), primary_key=True
    )
    status: Mapped[str] = mapped_column(
        ContactStatusPG, default=ContactStatus.REJECTED_BY_ME.value
    )
    my_user: Mapped[User] = relationship(
        User,
        foreign_keys=[my_user_id],
        back_populates='my_contacts',
        uselist=False,
    )
    other_user: Mapped[User] = relationship(
        User, foreign_keys=[other_user_id], uselist=False
    )
    __table_args__ = (
        UniqueConstraint(
            'my_user_id',
            'other_user_id',
            name=CNST.UQ_CNSTR_CONTACT_MY_USER_ID_TARGET_USER_ID,
        ),
    )


class Message(BaseWithIntPK):
    sender_id: Mapped[UUID_ID] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE')
    )
    receiver_id: Mapped[UUID_ID] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE')
    )
    text: Mapped[str] = mapped_column(
        String(CNST.MESSAGE_MAX_LENGTH), nullable=False
    )
    is_read: Mapped[bool] = mapped_column(default=False, nullable=False)
    sender: Mapped[User] = relationship(
        User,
        foreign_keys=[sender_id],
        back_populates='sent_messages',
        uselist=False,
    )
    receiver: Mapped[User] = relationship(
        User,
        foreign_keys=[receiver_id],
        back_populates='received_messages',
        uselist=False,
    )
