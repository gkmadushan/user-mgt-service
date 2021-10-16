from pydantic import BaseModel, Field
from typing import List, Optional

class UserGroup(BaseModel):
    user_id: str
    group_id: str

class CreateUser(BaseModel):
    id: Optional[str]
    email: str
    name: str
    role: str = Field(..., min=1, description="Role is required")
    groups: List[str] = []

class UpdateUser(BaseModel):
    name: str
    role: str = Field(..., min=1, description="Role is required")
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

class CreateGroup(BaseModel):
    id: Optional[str]
    name: str
    description: str

class UpdateGroup(BaseModel):
    name: str
    description: str
