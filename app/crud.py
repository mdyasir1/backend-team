from sqlalchemy.orm import Session
from sqlalchemy import text
from app import schemas
from typing import Dict, Any, List

def clean_and_flatten_skills(skills: List[str]) -> List[str]:
    """
    Takes a list of raw skill strings, splits any comma-separated entries, 
    strips whitespace, converts to lowercase, and returns a unique, sorted list 
    of individual skill names.
    """
    flat_skills = []
    for skill_string in skills:
        # Split by comma, then strip whitespace and convert to lowercase
        parts = [part.strip().lower() for part in skill_string.split(',')]
        flat_skills.extend(parts)
        
    # Remove any empty strings resulting from extra commas or poor input
    flat_skills = [s for s in flat_skills if s]

    # Use a set to remove duplicates, then convert back to a sorted list
    return sorted(list(set(flat_skills)))


def create_user(db: Session, user: schemas.UserCreate) -> Dict[str, Any]:
    """
    Creates a new user, or merges skills only if the submitted core data 
    (email, username, and location) matches the existing record.
    """
    
    # 1. INPUT CLEANING: De-duplicate and Normalize Skills using a set
    user_skills = clean_and_flatten_skills(user.skills)

    # Check for existing user by email
    existing_user_query = text("""
        SELECT user_id, username, email, location FROM users WHERE email = :email;
    """)
    existing_user_result = db.execute(existing_user_query, {"email": user.email}).fetchone()

    # Helper functions (omitted for brevity, they are the same as before)
    # ...
    def get_or_create_skill(skill_name: str) -> int:
        # DB ensures no duplicate skill names in the global 'skills' table.
        skill_result = db.execute(text("""
            INSERT INTO skills (skill_name)
            VALUES (:skill_name)
            ON CONFLICT (skill_name) DO UPDATE SET skill_name = EXCLUDED.skill_name
            RETURNING skill_id;
        """), {"skill_name": skill_name})
        return skill_result.fetchone().skill_id

    def get_existing_skills(user_id: int) -> List[str]:
        skills_query = text("""
            SELECT s.skill_name
            FROM user_skills us
            JOIN skills s ON us.skill_id = s.skill_id
            WHERE us.user_id = :user_id;
        """)
        return [row.skill_name for row in db.execute(skills_query, {"user_id": user_id}).fetchall()]
    # ...


    if existing_user_result:
        # ** Existing User Found: Check Core Data Match **
        
        # CRITICAL: Check if username AND location match the existing record
        if (existing_user_result.username != user.username or 
            existing_user_result.location != user.location):
            
            # Core data (username or location) does NOT match. Block the submission.
            db.rollback() 
            return {
                "status_code": 409, 
                "message": "email already exsits" # Blocking message for conflict
            }

        # Core data MATCHES. Proceed with Skill Merge logic.
        user_id = existing_user_result.user_id
        
        existing_skills = get_existing_skills(user_id)
        
        # Determine which skills are new for this user
        new_skills_to_add = set(user_skills) - set(existing_skills)
        
        if not new_skills_to_add:
            # User exists, and all submitted skills already exist for this user.
            db.rollback() 
            return {
                "status_code": 409, 
                "message": "user already exsits"
            }

        # Add new skills only
        added_skill_names = []
        for skill_name in new_skills_to_add:
            skill_id = get_or_create_skill(skill_name)

            db.execute(text("""
                INSERT INTO user_skills (user_id, skill_id)
                VALUES (:user_id, :skill_id)
                ON CONFLICT (user_id, skill_id) DO NOTHING;
            """), {"user_id": user_id, "skill_id": skill_id})
            added_skill_names.append(skill_name)
        
        db.commit()
        
        # Combine existing and newly added skills using a set to eliminate any duplicates.
        final_skills_set = set(existing_skills)
        final_skills_set.update(added_skill_names)
        newly_updated_skills = sorted(list(final_skills_set))
        
        return {
            "status_code": 200,
            "message": f"the previous skills are unchanged and the newly added skills are added: {', '.join(added_skill_names)}",
            "user_data": {
                "user_id": user_id,
                "username": existing_user_result.username, 
                "email": existing_user_result.email,       
                "location": existing_user_result.location, 
                "skills": newly_updated_skills 
            }
        }

    else:
        # ** New User Creation **
        
        # 2. Insert user
        try:
            result = db.execute(text("""
                INSERT INTO users (username, email, location)
                VALUES (:username, :email, :location)
                RETURNING user_id, username, email, location;
            """), {
                "username": user.username,
                "email": user.email,
                "location": user.location
            })
            db_user = result.fetchone()
            user_id = db_user.user_id
        except Exception as e:
            db.rollback()
            if "duplicate key value violates unique constraint" in str(e):
                 return {
                    "status_code": 409, 
                    "message": "email already exsits"
                }
            raise e

        # 3. Insert skills and map to user (using the cleaned input)
        for skill in user_skills:
            skill_id = get_or_create_skill(skill)

            db.execute(text("""
                INSERT INTO user_skills (user_id, skill_id)
                VALUES (:user_id, :skill_id)
                ON CONFLICT (user_id, skill_id) DO NOTHING;
            """), {"user_id": user_id, "skill_id": skill_id})

        db.commit()

        return {
            "status_code": 201, # Created status
            "message": "new user data submission",
            "user_data": {
                "user_id": db_user.user_id,
                "username": db_user.username,
                "email": db_user.email,
                "location": db_user.location,
                "skills": user_skills 
            }
        }

def get_users(db: Session):
    # This function is unchanged and correctly retrieves unique skills
    query = text("""
        SELECT u.user_id, u.username, u.email, u.location, s.skill_name
        FROM users u
        LEFT JOIN user_skills us ON u.user_id = us.user_id
        LEFT JOIN skills s ON us.skill_id = s.skill_id
        ORDER BY u.user_id;
    """)
    result = db.execute(query).fetchall()

    users_dict = {}
    for row in result:
        if row.user_id not in users_dict:
            users_dict[row.user_id] = {
                "user_id": row.user_id,
                "username": row.username,
                "email": row.email,
                "location": row.location,
                "skills": []
            }
        # De-duplication check for the final API output list
        if row.skill_name and row.skill_name not in users_dict[row.user_id]["skills"]:
            users_dict[row.user_id]["skills"].append(row.skill_name)

    return list(users_dict.values())