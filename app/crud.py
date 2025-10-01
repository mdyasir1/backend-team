from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload 
from fastapi import HTTPException
from . import models, schemas
from sqlalchemy.dialects import postgresql as pg

# --- Helper to get or create a skill ---
async def get_or_create_skill(db: AsyncSession, skill_name: str) -> models.Skill:
    # 1. Try to select the skill
    stmt = select(models.Skill).where(models.Skill.skill_name == skill_name)
    result = await db.execute(stmt)
    skill = result.scalars().first()
    
    if skill:
        return skill
    
    # 2. If skill doesn't exist, create it
    new_skill = models.Skill(skill_name=skill_name)
    db.add(new_skill)
    # We don't commit here, as it's part of the larger transaction
    await db.flush() 
    return new_skill

# --- POST Logic: Create a user and map skills ---
async def create_submission(db: AsyncSession, submission: schemas.SubmissionCreate):
    # 1. Check if user already exists (by email)
    user_stmt = select(models.User).where(models.User.email == submission.email)
    user_result = await db.execute(user_stmt)
    existing_user = user_result.scalars().first()

    if existing_user:
        raise HTTPException(status_code=400, detail="User with this email already exists.")

    # 2. Create the new user
    new_user = models.User(
        username=submission.username,
        location=submission.location,
        email=submission.email
    )
    db.add(new_user)
    await db.flush() # Get the new_user.user_id before committing

    # 3. Process skills and create UserSkill mappings
    for skill_name in submission.skills:
        skill = await get_or_create_skill(db, skill_name)
        
        # Create the junction table entry (no proficiency_level field required)
        user_skill = models.UserSkill(
            user_id=new_user.user_id, 
            skill_id=skill.skill_id
        )
        db.add(user_skill)

    try:
        await db.commit()
        # For a POST request, we typically return the created object
        # Note: SQLAlchemy relationships handle the fetching of linked data.
        # We need to re-fetch the user with loaded skills for the response model.
        await db.refresh(new_user, attribute_names=["skills"]) 
        return new_user
    except Exception as e:
        await db.rollback()
        # Log the error for debugging
        print(f"Database error during submission: {e}")
        raise HTTPException(status_code=400, detail=f"Database error: {e}")

# --- GET Logic: Fetch users with all their skills ---
async def get_submissions(db: AsyncSession, skip: int = 0, limit: int = 50):
    try:
        # Construct the query with eager loading for the 'skills' relationship
        stmt = select(models.User).options(
            selectinload(models.User.skills) 
        ).offset(skip).limit(limit)
        
        # Execute the asynchronous query
        result = await db.execute(stmt)
        
        # Get all unique User objects, preventing duplicates from the join
        users = result.scalars().unique().all()
        
        return users
    
    except Exception as e:
        # Logging the error is helpful for debugging 
        print(f"Error fetching submissions: {e}") 
        # Reraise as an HTTP exception for the router to handle (or handle it in the router)
        raise HTTPException(status_code=500, detail=f"Database query failed: {str(e)}")