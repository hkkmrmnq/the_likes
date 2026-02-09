from pydantic import BaseModel, Field

from src.config import CFG


class AccessToken(BaseModel):
    access_token: str
    token_type: str = 'Access'


confirmation_code_field = Field(ge=0, lt=10**CFG.CONFIRMATION_CODE_LENGTH)


class EmailVerificationData(BaseModel):
    email: str
    code: int = confirmation_code_field


class UserCredentials(BaseModel):
    email: str
    password: str


class EmailSchema(BaseModel):
    email: str


class ChangePasswordSchema(BaseModel):
    email: str
    password: str
    code: int = confirmation_code_field
