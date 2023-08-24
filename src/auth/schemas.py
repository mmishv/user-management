from pydantic import BaseModel, EmailStr


class JwtResponse(BaseModel):
    access_token: str
    refresh_token: str


class JwtRequest(BaseModel):
    username: str
    user_id: str
    role: str


class UserLogin(BaseModel):
    username: str
    password: str


class UserSignup(BaseModel):
    username: str
    email: EmailStr
    password: str


class UserResetPassword(BaseModel):
    reset_token: str
    new_password: str


class UserEmail(BaseModel):
    email: EmailStr
