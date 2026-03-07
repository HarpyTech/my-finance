from pydantic import BaseModel, EmailStr, Field


class UserCreate(BaseModel):
    username: EmailStr
    password: str = Field(min_length=8)


class UserLogin(BaseModel):
    username: EmailStr
    password: str


class UserPublic(BaseModel):
    username: EmailStr
    role: str


class UserInDB(UserPublic):
    password_hash: str
