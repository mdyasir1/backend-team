from pydantic import BaseModel, EmailStr
from typing import List, Optional

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    location: str
    skills: List[str]

class UserResponse(BaseModel):
    user_id: int
    username: str
    email: EmailStr
    location: str
    skills: List[str]

class SubmissionStatus(BaseModel):
    message: str
    user_data: Optional[UserResponse] = None