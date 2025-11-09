import inspect
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Integer, String, text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.exc import MissingGreenlet
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from src.config import constants as CNST
from src.config.config import CFG
from src.context import get_current_language
from src.db.base import BaseWithIntPK
from src.exceptions.exceptions import ServerError
from src.logger import logger

if TYPE_CHECKING:
    from .personal_values import (
        PersonalAspect,
        PersonalValue,
        UniqueValueAspectLink,
    )
    from .translations import (
        AspectTranslation,
        AttitudeTranslation,
        ValueTranslation,
    )
    from .user_and_profile import Profile


def _translate_attribute(self: 'Value | Aspect | Attitude'):
    """
    If current language ContextVar != CFG.DEFAULT_LANGUAGE -
    returns translated version of an attribute.
    Related Translations must be eagerly loaded -
    otherwise default attribute will be returned.
    """
    current_frame = inspect.currentframe()
    if current_frame is None or current_frame.f_back is None:
        msg = 'current_frame / current_frame.f_back is None'
        logger.error(msg)
        raise ServerError(msg)
    lan_code = get_current_language()
    attr_name = current_frame.f_back.f_code.co_name
    if lan_code != CFG.DEFAULT_LANGUAGE and lan_code in CFG.TRANSLATE_TO:
        try:
            for translation in self.translations:
                if translation.language_code == lan_code:
                    translation = translation
                    return getattr(translation, attr_name)
        except MissingGreenlet:
            logger.error(
                (
                    f'_translate_attribute MissingGreenlet, {lan_code=}. '
                    'Translations not loaded?'
                )
            )
    return getattr(self, f'{attr_name}_default')


class Value(BaseWithIntPK):
    name_default: Mapped[str] = mapped_column(
        String(CNST.VALUE_NAME_MAX_LENGTH), unique=True, nullable=False
    )
    aspects: Mapped[list['Aspect']] = relationship(
        'Aspect', back_populates='value', cascade='all, delete-orphan'
    )
    translations: Mapped[list['ValueTranslation']] = relationship(
        'ValueTranslation',
        back_populates='value',
        cascade='all, delete-orphan',
    )
    personal_values: Mapped[list['PersonalValue']] = relationship(
        'PersonalValue',
        back_populates='value',
        cascade='all, delete-orphan',
    )
    unique_values: Mapped[list['UniqueValue']] = relationship(
        'UniqueValue',
        back_populates='value',
        cascade='all, delete-orphan',
    )

    @property
    def name(self) -> str:
        """Return translated name or fallback to default."""
        return _translate_attribute(self)


class Aspect(BaseWithIntPK):
    key_phrase_default: Mapped[str] = mapped_column(
        String(CNST.SUBDEF_KEY_PHRASE_MAXLENGTH), nullable=False
    )
    statement_default: Mapped[str] = mapped_column(
        String(CNST.SUBDEF_STATEMENT_MAX_LENGTH), nullable=False
    )
    value_id: Mapped[int] = mapped_column(
        ForeignKey('values.id', ondelete='CASCADE')
    )
    unique_value_id: Mapped[int | None] = mapped_column(
        ForeignKey('uniquevalues.id', ondelete='SET NULL'), nullable=True
    )
    value: Mapped['Value'] = relationship(
        'Value',
        back_populates='aspects',
        uselist=False,
    )
    uv_links: Mapped[list['UniqueValueAspectLink']] = relationship(
        'UniqueValueAspectLink', back_populates='aspect'
    )
    translations: Mapped[list['AspectTranslation']] = relationship(
        'AspectTranslation',
        back_populates='aspect',
        cascade='all, delete-orphan',
    )
    personal_aspects: Mapped[list['PersonalAspect']] = relationship(
        'PersonalAspect',
        back_populates='aspect',
        cascade='all, delete-orphan',
    )

    @property
    def key_phrase(self) -> str:
        """Return translated key_phrase or fallback to default."""
        return _translate_attribute(self)

    @property
    def statement(self) -> str:
        """Return translated statement or fallback to default."""
        return _translate_attribute(self)


class UniqueValue(BaseWithIntPK):
    """Represents unique combination of Aspects for particular Value."""

    value_id: Mapped[int] = mapped_column(
        Integer, ForeignKey('values.id', ondelete='CASCADE')
    )
    aspect_ids: Mapped[list[int]] = mapped_column(ARRAY(Integer))
    value: Mapped[Value] = relationship(
        'Value', back_populates='unique_values', uselist=False
    )
    aspect_links: Mapped[list['UniqueValueAspectLink']] = relationship(
        'UniqueValueAspectLink', back_populates='unique_value'
    )
    personal_values: Mapped[list['PersonalValue']] = relationship(
        'PersonalValue',
        back_populates='unique_value',
        cascade='all, delete-orphan',
    )
    __table_args__ = (
        Index(
            'uq_non_empty_aspect_ids',
            'aspect_ids',
            unique=True,
            postgresql_where=text("aspect_ids <> '{}'"),
        ),
    )


class Attitude(BaseWithIntPK):
    """Represents general attitude to moral values as such."""

    statement_default: Mapped[str] = mapped_column(
        String(CNST.ATTITUDE_TEXT_MAX_LENGTH), unique=True
    )
    profiles: Mapped[list['Profile']] = relationship(
        'Profile', back_populates='attitude'
    )
    translations: Mapped[list['AttitudeTranslation']] = relationship(
        'AttitudeTranslation', back_populates='attitude'
    )

    @property
    def statement(self) -> str:
        """Return translated statement or fallback to default."""
        return _translate_attribute(self)
