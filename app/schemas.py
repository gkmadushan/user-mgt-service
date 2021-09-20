from pydantic import BaseModel
from typing import List, Optional

class UserGroup(BaseModel):
    user_id: str
    group_id: str

class CreateUser(BaseModel):
    id: Optional[str]
    email: str
    name: str
    role: str
    groups: List[str] = []

class ConfirmUser(BaseModel):
    password: str
    otp: str

class ConfigureOTP(BaseModel):
    token: str
    otp: str

class AuthDetails(BaseModel):
    username: str
    password: str

