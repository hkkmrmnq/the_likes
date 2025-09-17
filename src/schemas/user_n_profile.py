from uuid import UUID

from fastapi_users import schemas
from geoalchemy2.shape import to_shape
from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    HttpUrl,
    ValidationError,
    computed_field,
    field_serializer,
    field_validator,
)
from pydantic_extra_types.coordinate import Latitude, Longitude

from .. import constants as cnst


class UserRead(schemas.BaseUser[UUID]):
    id: UUID
    email: str

    class Config:
        arbitrary_types_allowed = True


class UserCreate(schemas.BaseUserCreate):
    email: EmailStr = Field(
        max_length=cnst.EMAIL_MAX_LENGTH, examples=['johndoe@example.com']
    )
    password: str = Field(
        min_length=cnst.PASSWORD_MIN_LENGTH,
        max_length=cnst.PASSWORD_MAX_LENGTH,
        examples=['z2t6KUyJu3QB'],
    )


class UserUpdate(schemas.BaseUserUpdate):
    email: EmailStr | None = Field(
        max_length=cnst.EMAIL_MAX_LENGTH,
        examples=['johndoe@example.com'],
        default=None,
    )
    password: str | None = Field(
        min_length=cnst.PASSWORD_MIN_LENGTH,
        max_length=cnst.PASSWORD_MAX_LENGTH,
        examples=['z2t6KUyJu3QB'],
        default=None,
    )


class ProfileRead(BaseModel):
    name: str | None
    languages: list[str]
    location: str | None
    distance_limit: int | None
    avatar: str | None

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


class ComputedLocationMixin(BaseModel):
    longitude: Longitude | None
    latitude: Latitude | None

    @computed_field
    @property
    def location(self) -> str | None:
        if all((self.longitude, self.latitude)):
            return f'POINT({self.longitude} {self.latitude})'


class AvatarFieldMixin(BaseModel):
    avatar: HttpUrl | None = Field(max_length=cnst.URL_MAX_LENGTH)

    @field_serializer('avatar')
    def serialize_avatar(self, avatar: HttpUrl | None) -> str | None:
        return str(avatar) if avatar else None


class ProfileUpdate(AvatarFieldMixin, ComputedLocationMixin):
    name: str | None = Field(
        max_length=cnst.USER_NAME_MAX_LENGTH,
        examples=['John Doe'],
    )
    distance_limit: int | None = Field(gt=0, le=cnst.DISTANCE_MAX_LIMIT)
    languages: list[str]

    @field_validator('languages', mode='after')
    def validate_languages(cls, languages):
        wrong = set(languages) - set(cnst.SUPPORTED_LANGUAGES)
        if len(wrong) > 0:
            raise ValidationError(
                f'Incorrect language(s): {", ".join([lang for lang in wrong])}'
            )
        return languages
