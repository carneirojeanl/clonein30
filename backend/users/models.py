from pydantic import BaseModel, Field

class User(BaseModel):
    username: str
    first_name: str
    last_name: str
    is_admin: bool
    credits: int


class CreateUser(BaseModel):
    username: str = Field(min_length=3, max_length=20)
    password: str = Field(min_length=6, max_length=20)
    first_name: str = Field(min_length=1, max_length=50)
    last_name: str = Field(min_length=1, max_length=50)