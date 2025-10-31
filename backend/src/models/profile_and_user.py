from uuid import UUID

from fastapi_users import schemas as fu_schemas
from geoalchemy2.shape import to_shape
from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    ValidationError,
    computed_field,
    field_validator,
)
from pydantic_extra_types.coordinate import Latitude, Longitude

from src.config import CFG
from src.config import constants as CNST


class UserRead(fu_schemas.BaseUser[UUID]):
    id: UUID
    email: str

    class Config:
        arbitrary_types_allowed = True


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
    location: str | None
    distance_limit: int | None
    recommend_me: bool

    class Config:
        from_attributes = True
        arbitrary_types_allowed = True

    @field_validator('location', mode='before')
    @classmethod
    def convert_wkb_to_wkt(cls, loaction):
        if loaction is not None:
            loaction = loaction
            return str(to_shape(loaction))
        return loaction


class ProfileUpdate(BaseModel):
    name: str | None = Field(
        max_length=CNST.USER_NAME_MAX_LENGTH,
        examples=['John Doe'],
    )
    longitude: Longitude | None
    latitude: Latitude | None
    distance_limit: int | None = Field(gt=0, le=CNST.DISTANCE_LIMIT_MAX)
    languages: list[str]
    recommend_me: bool

    @computed_field
    @property
    def location(self) -> str | None:
        if all((self.longitude, self.latitude)):
            return f'POINT({self.longitude} {self.latitude})'

    @field_validator('languages', mode='after')
    def validate_languages(cls, languages):
        wrong = set(languages) - set(CFG.SUPPORTED_LANGUAGES)
        if len(wrong) > 0:
            raise ValidationError(
                f'Incorrect language(s): {", ".join([lang for lang in wrong])}'
            )
        return languages
