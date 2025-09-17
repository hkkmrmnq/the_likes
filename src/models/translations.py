from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..constants import (
    ATTITUDE_TEXT_MAX_LENGTH,
    SUBDEF_KEY_PHRASE_MAXLENGTH,
    SUBDEF_STATEMENT_MAX_LENGTH,
    VALUE_NAME_MAX_LENGTH,
)
from .base import BaseWithIntPK

if TYPE_CHECKING:
    from .core import Aspect, ValueTitle
    from .user_profile import Attitude


class TranslationBase(BaseWithIntPK):
    __abstract__ = True
    language_code: Mapped[str] = mapped_column(String(2))


class ValueTitleTranslation(TranslationBase):
    name: Mapped[str] = mapped_column(String(VALUE_NAME_MAX_LENGTH))
    value_title_id: Mapped[int] = mapped_column(
        ForeignKey('valuetitles.id', ondelete='CASCADE')
    )
    value_title: Mapped['ValueTitle'] = relationship(
        'ValueTitle',
        back_populates='translations',
        uselist=False,
    )


class AspectTranslation(TranslationBase):
    key_phrase: Mapped[str] = mapped_column(
        String(SUBDEF_KEY_PHRASE_MAXLENGTH)
    )
    statement: Mapped[str] = mapped_column(String(SUBDEF_STATEMENT_MAX_LENGTH))
    aspect_id: Mapped[int] = mapped_column(
        ForeignKey('aspects.id', ondelete='CASCADE')
    )
    aspect: Mapped['Aspect'] = relationship(
        'Aspect',
        back_populates='translations',
        uselist=False,
    )


class AttitudeTranslation(TranslationBase):
    attitude_id: Mapped[int] = mapped_column(
        ForeignKey('attitudes.id', ondelete='CASCADE')
    )
    statement: Mapped[str] = mapped_column(String(ATTITUDE_TEXT_MAX_LENGTH))
    attitude: Mapped['Attitude'] = relationship(
        'Attitude', back_populates='translations', uselist=False
    )
