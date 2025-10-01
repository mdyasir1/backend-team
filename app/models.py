from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, ForeignKey, UniqueConstraint, func, DateTime
from app.database import Base

# Base = declarative_base()

# --- Junction Table Model ---
class UserSkill(Base):
    __tablename__ = "user_skills"
    
    user_skill_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.user_id', ondelete='CASCADE'), nullable=False)
    skill_id = Column(Integer, ForeignKey('skills.skill_id', ondelete='CASCADE'), nullable=False)
    # The database team said this is not required, so we omit it from the model:
    # proficiency_level = Column(String(50)) 
    
    __table_args__ = (
        UniqueConstraint('user_id', 'skill_id', name='unique_user_skill'),
    )

# --- User Model ---
class User(Base):
    __tablename__ = "users"
    
    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), nullable=False) # Changed from 'name' to 'username'
    email = Column(String(100), unique=True, nullable=False)
    location = Column(String(100))
    # Note: Your old 'created_at' and 'id' columns map to 'user_id' here
    
    # Relationship to Skills through the junction table
    skills = relationship("Skill", secondary="user_skills", back_populates="users")
    
# --- Skill Model ---
class Skill(Base):
    __tablename__ = "skills"
    
    skill_id = Column(Integer, primary_key=True, index=True)
    skill_name = Column(String(100), nullable=False, unique=True)
    
    # Relationship back to Users
    users = relationship("User", secondary="user_skills", back_populates="skills")
