import inspect
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, Index, Integer, String, text
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship,
)

from src import exceptions as exc
from src.config import CFG
from src.config import constants as CNST
from src.context import get_current_language
from src.db.base import BaseWithIntPK

if TYPE_CHECKING:
    from .personal_values import (
        PersonalAspect,
        PersonalValue,
        UniqueValueAspectLink,
    )
    from .profile_and_user import Profile
    from .translations import (
        AspectTranslation,
        AttitudeTranslation,
        ValueTranslation,
    )


def _translate_attribute(self: 'Value | Aspect | Attitude'):
    current_frame = inspect.currentframe()
    lan_code = get_current_language()
    if current_frame is None or current_frame.f_back is None:
        raise exc.ServerError('current_frame / current_frame.f_back is None')
    attr_name = current_frame.f_back.f_code.co_name
    if (
        lan_code != CFG.DEFAULT_LANGUAGE
        and lan_code in CFG.SUPPORTED_LANGUAGES
    ):
        for translation in self.translations:
            if translation.language_code == lan_code:
                return getattr(translation, attr_name)
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

    @hybrid_property
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

    @hybrid_property
    def key_phrase(self) -> str:
        """Return translated key_phrase or fallback to default"""
        return _translate_attribute(self)

    @hybrid_property
    def statement(self) -> str:
        """Return translated statement or fallback to default"""
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
    statement_default: Mapped[str] = mapped_column(
        String(CNST.ATTITUDE_TEXT_MAX_LENGTH), unique=True
    )
    profiles: Mapped[list['Profile']] = relationship(
        'Profile', back_populates='attitude'
    )
    translations: Mapped[list['AttitudeTranslation']] = relationship(
        'AttitudeTranslation', back_populates='attitude'
    )

    @hybrid_property
    def statement(self) -> str:
        """Return translated statement or fallback to default"""
        return _translate_attribute(self)
