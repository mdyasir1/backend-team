from pydantic import BaseModel, EmailStr
from typing import List, Optional

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

# New schema for the custom response when submitting a form
class SubmissionStatus(BaseModel):
    message: str
    user_data: Optional[UserResponse] = None # Optional user data for new/updated users