from pydantic import BaseModel


class AccessToken(BaseModel):
    access_token: str
    token_type: str = 'Access'


class EmailVerificationCode(BaseModel):
    email: str
    code: int


class UserCredentials(BaseModel):
    email: str
    password: str
