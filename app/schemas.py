from pydantic import BaseModel

class CreateUser(BaseModel):
    email: str
    name: str

class AuthDetails(BaseModel):
    username: str
    password: str