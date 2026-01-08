from uuid import UUID

from fastapi_users import schemas as fu_schemas
from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    ValidationError,
    field_validator,
    model_validator,
)
from pydantic_extra_types.coordinate import Latitude, Longitude

from src.config import constants as CNST
from src.config.config import CFG


class UserRead(fu_schemas.BaseUser[UUID]):
    id: UUID
    email: str

    model_config = {'arbitrary_types_allowed': True}


class UserCreate(fu_schemas.BaseUserCreate):
    email: EmailStr = Field(
        max_length=CNST.EMAIL_MAX_LENGTH, examples=['johndoe@example.com']
    )
    password: str = Field(
        min_length=CNST.PASSWORD_MIN_LENGTH,
        max_length=CNST.PASSWORD_MAX_LENGTH,
        examples=['z2t6KUyJu3QB'],
    )


class UserUpdate(fu_schemas.BaseUserUpdate):
    email: EmailStr | None = Field(
        max_length=CNST.EMAIL_MAX_LENGTH,
        examples=['johndoe@example.com'],
        default=None,
    )
    password: str | None = Field(
        min_length=CNST.PASSWORD_MIN_LENGTH,
        max_length=CNST.PASSWORD_MAX_LENGTH,
        examples=['z2t6KUyJu3QB'],
        default=None,
    )


class ProfileRead(BaseModel):
    name: str | None
    languages: list[str]
    distance_limit: float | None
    recommend_me: bool
    longitude: Longitude | None
    latitude: Latitude | None

    model_config = {'from_attributes': True, 'arbitrary_types_allowed': True}


class ProfileUpdate(BaseModel):
    name: str | None = Field(
        max_length=CNST.USER_NAME_MAX_LENGTH,
        examples=['John Doe'],
    )
    longitude: Longitude | None
    latitude: Latitude | None
    distance_limit: float | None = Field(gt=0, le=CNST.DISTANCE_LIMIT_KM_MAX)
    languages: list[str]
    recommend_me: bool

    @field_validator('languages', mode='after')
    def validate_languages(cls, languages):
        wrong = set(languages) - set(CFG.SUPPORTED_LANGUAGES)
        if len(wrong) > 0:
            raise ValidationError(
                f'Incorrect language(s): {", ".join([lang for lang in wrong])}'
            )
        return languages

    @model_validator(mode='after')
    def validate_distance_limit(self):
        if ((self.longitude is None) | (self.latitude is None)) & (
            self.distance_limit is not None
        ):
            raise ValidationError('Location required for distance_limit.')
        return self
