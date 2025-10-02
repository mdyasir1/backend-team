from pydantic import BaseModel, EmailStr
from typing import List

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    location: str
    skills: List[str]  # list of skills for the user

class UserResponse(BaseModel):
    user_id: int
    username: str
    email: EmailStr
    location: str
    skills: List[str]
