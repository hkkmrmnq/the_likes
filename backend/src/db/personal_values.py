from uuid import UUID

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.config import CFG, ENM

from .base import Base, BaseWithIntPK
from .core import Aspect, UniqueValue, Value
from .user_and_profile import User


class UniqueValueAspectLink(Base):
    """UniqueValue/Aspect link model."""

    unique_value_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('uniquevalues.id', ondelete='CASCADE'),
        primary_key=True,
    )
    aspect_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('aspects.id', ondelete='CASCADE'),
        primary_key=True,
    )
    unique_value: Mapped[UniqueValue] = relationship(
        UniqueValue, back_populates='aspect_links', uselist=False
    )
    aspect: Mapped[Aspect] = relationship(
        Aspect, back_populates='uv_links', uselist=False
    )


class PersonalValue(BaseWithIntPK):
    """User/Value link model."""

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE'),
    )
    value_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('values.id', ondelete='CASCADE')
    )
    unique_value_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('uniquevalues.id', ondelete='CASCADE')
    )
    polarity: Mapped[str] = mapped_column(ENM.PolarityPG)
    user_order: Mapped[int] = mapped_column(Integer)
    user: Mapped[User] = relationship(
        User, back_populates='personal_values', uselist=False
    )
    value: Mapped[Value] = relationship(
        Value, back_populates='personal_values', uselist=False
    )
    unique_value: Mapped[UniqueValue] = relationship(
        UniqueValue, back_populates='personal_values', uselist=False
    )
    personal_aspects: Mapped[list['PersonalAspect']] = relationship(
        'PersonalAspect', back_populates='personal_value'
    )
    __table_args__ = (
        CheckConstraint(
            CFG.PERSONAL_VALUE_MAX_ORDER_CONSTRAINT_TEXT,
            name='max_user_order',
        ),
        CheckConstraint('user_order >= 1', name='min_user_order'),
        UniqueConstraint('user_id', 'value_id', name='uq_user_id_value_id'),
        Index(
            'unique_personal_value_order',
            'user_id',
            'value_id',
            'user_order',
            unique=True,
        ),
    )


class PersonalAspect(BaseWithIntPK):
    """User/Aspect link model."""

    user_id: Mapped[UUID] = mapped_column(
        ForeignKey('users.id', ondelete='CASCADE'),
    )
    aspect_id: Mapped[int] = mapped_column(
        ForeignKey('aspects.id', ondelete='CASCADE'),
    )
    included: Mapped[bool] = mapped_column(Boolean)
    personal_value_id: Mapped[int] = mapped_column(
        ForeignKey('personalvalues.id', ondelete='CASCADE')
    )
    user: Mapped[User] = relationship(
        User, back_populates='personal_aspects', uselist=False
    )
    aspect: Mapped[Aspect] = relationship(
        Aspect,
        back_populates='personal_aspects',
        uselist=False,
    )
    personal_value: Mapped[PersonalValue] = relationship(
        PersonalValue, back_populates='personal_aspects', uselist=False
    )
    __table_args__ = (
        UniqueConstraint(
            'user_id',
            'aspect_id',
            name='user_aspect_unique_constraint',
        ),
    )
