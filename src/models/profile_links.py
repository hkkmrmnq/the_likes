from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Index,
    Integer,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import ENUM
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..config import constants as CNST
from .base import Base, BaseWithIntPK

if TYPE_CHECKING:
    from .core import Aspect, UniqueValue, ValueTitle
    from .user_profile import Profile


class UniqueValueAspectLink(Base):
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
    unique_value: Mapped['ValueTitle'] = relationship(
        'UniqueValue', back_populates='aspect_links', uselist=False
    )
    aspect: Mapped['Aspect'] = relationship(
        'Aspect', back_populates='uv_links', uselist=False
    )


polarity = ENUM(
    'positive',
    'negative',
    'neutral',
    name='polarity_enum',
    create_type=True,
)


class ProfileValueLink(BaseWithIntPK):
    polarity: Mapped[str] = mapped_column(polarity)
    user_order: Mapped[int] = mapped_column(Integer)
    profile_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('profiles.id', ondelete='CASCADE'),
    )
    value_title_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('valuetitles.id', ondelete='CASCADE')
    )
    unique_value_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('uniquevalues.id', ondelete='CASCADE')
    )
    profile: Mapped['Profile'] = relationship(
        'Profile', back_populates='value_links', uselist=False
    )
    value_title: Mapped['ValueTitle'] = relationship(
        'ValueTitle', back_populates='profile_links', uselist=False
    )
    unique_value: Mapped['UniqueValue'] = relationship(
        'UniqueValue', back_populates='profile_links', uselist=False
    )
    profile_aspect_links: Mapped[list['ProfileAspectLink']] = relationship(
        'ProfileAspectLink', back_populates='profile_value_link'
    )
    __table_args__ = (
        CheckConstraint(
            CNST.MAX_USER_ORDER_CONSTRAINT_TEXT,
            name='max_user_order',
        ),
        CheckConstraint(
            CNST.MIN_USER_ORDER_CONSTRAINT_TEXT,
            name='min_user_order',
        ),
        UniqueConstraint(
            'profile_id', 'value_title_id', name='profile_value_unique'
        ),
        Index(
            'unique_profile_value_order',
            'profile_id',
            'value_title_id',
            'user_order',
            unique=True,
        ),
    )


class ProfileAspectLink(BaseWithIntPK):
    included: Mapped[bool] = mapped_column(Boolean)
    profile_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('profiles.id', ondelete='CASCADE'),
    )
    aspect_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey('aspects.id', ondelete='CASCADE'),
    )
    profile_value_link_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('profilevaluelinks.id', ondelete='CASCADE')
    )
    profile: Mapped['Profile'] = relationship(
        'Profile', back_populates='aspect_links', uselist=False
    )
    aspect: Mapped['Aspect'] = relationship(
        'Aspect',
        back_populates='profile_links',
        uselist=False,
    )
    profile_value_link: Mapped[ProfileValueLink] = relationship(
        ProfileValueLink, back_populates='profile_aspect_links', uselist=False
    )
    __table_args__ = (
        UniqueConstraint(
            'profile_id',
            'aspect_id',
            name='profile_aspect_unique_constraint',
        ),
    )
