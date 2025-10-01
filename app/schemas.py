from pydantic import BaseModel, EmailStr, constr, Field
from pydantic import ConfigDict
from typing import List, Optional
from datetime import datetime

# --- Incoming Data Schema (for POST request) ---
class SubmissionCreate(BaseModel):
    # Field names changed to match new 'users' table columns
    username: constr(strip_whitespace=True, min_length=1, max_length=100)
    location: Optional[constr(strip_whitespace=True, max_length=100)] = None
    email: EmailStr
    # List of skill names (strings) provided by the user
    skills: List[constr(min_length=1, max_length=100)] = Field(default_factory=list)

# --- Outgoing Data Schemas (for GET request) ---
class SkillSchema(BaseModel):
    skill_name: str
    
    class Config:
        # from_attributes = True
        model_config = ConfigDict(from_attributes=True)

class SubmissionResponse(BaseModel):
    user_id: int
    username: str
    email: EmailStr
    location: Optional[str]
    # The 'skills' field is now a list of SkillSchema objects
    skills: List[SkillSchema] = []

    class Config:
        # from_attributes = True
        model_config = ConfigDict(from_attributes=True)