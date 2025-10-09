from sqlalchemy.orm import Session
from sqlalchemy import text
from app import schemas
from typing import Dict, Any, List

def create_user(db: Session, user: schemas.UserCreate) -> Dict[str, Any]:
    """
    Creates a new user or merges new skills if the user (identified by email) already exists.
    Skills are robustly de-duplicated from the input and in the final response.
    Core user data (username, location) is not updated for existing users.
    """
    
    # --- Input Cleaning: De-duplicate and Normalize Skills ---
    # This removes any duplicates submitted in the user's input list.
    user_skills = sorted(list(set(user.skills)))

    # 1. Check for existing user by email
    existing_user_query = text("""
        SELECT user_id, username, email, location FROM users WHERE email = :email;
    """)
    existing_user_result = db.execute(existing_user_query, {"email": user.email}).fetchone()

    # Helper function to get skill_id
    def get_or_create_skill(skill_name: str) -> int:
        # ON CONFLICT (skill_name) ensures no duplicate entries in the global 'skills' table.
        skill_result = db.execute(text("""
            INSERT INTO skills (skill_name)
            VALUES (:skill_name)
            ON CONFLICT (skill_name) DO UPDATE SET skill_name = EXCLUDED.skill_name
            RETURNING skill_id;
        """), {"skill_name": skill_name})
        return skill_result.fetchone().skill_id

    # Helper function to get existing user skills
    def get_existing_skills(user_id: int) -> List[str]:
        skills_query = text("""
            SELECT s.skill_name
            FROM user_skills us
            JOIN skills s ON us.skill_id = s.skill_id
            WHERE us.user_id = :user_id;
        """)
        return [row.skill_name for row in db.execute(skills_query, {"user_id": user_id}).fetchall()]


    if existing_user_result:
        # ** Existing User Found: Check and Merge Skills **
        user_id = existing_user_result.user_id
        
        # Get current skills
        existing_skills = get_existing_skills(user_id)
        
        # Determine which skills are new for this user (using the cleaned input)
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

            # ON CONFLICT (user_id, skill_id) DO NOTHING prevents duplicate entries 
            # in the 'user_skills' mapping table.
            db.execute(text("""
                INSERT INTO user_skills (user_id, skill_id)
                VALUES (:user_id, :skill_id)
                ON CONFLICT (user_id, skill_id) DO NOTHING;
            """), {"user_id": user_id, "skill_id": skill_id})
            added_skill_names.append(skill_name)
        
        db.commit()
        
        # --- Ensure the final list of skills for the response is de-duplicated ---
        # Combine existing and newly added skills using a set to eliminate any duplicates.
        final_skills_set = set(existing_skills)
        final_skills_set.update(added_skill_names)
        newly_updated_skills = sorted(list(final_skills_set))
        
        return {
            "status_code": 200,
            "message": f"the previous skills are unchanged and the newly added skills are added: {', '.join(added_skill_names)}",
            "user_data": {
                "user_id": user_id,
                # Returning the existing data (No updates to core fields)
                "username": existing_user_result.username, 
                "email": existing_user_result.email,       
                "location": existing_user_result.location, 
                "skills": newly_updated_skills # Return the robustly de-duplicated list
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
            # Safety net for DB unique constraint violation if initial select somehow failed (race condition)
            if "duplicate key value violates unique constraint" in str(e):
                 return {
                    "status_code": 409, 
                    "message": "user already exsits"
                }
            raise e

        # 3. Insert skills and map to user (using the cleaned input)
        for skill in user_skills:
            skill_id = get_or_create_skill(skill)

            # Insert mapping into user_skills
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
                # Return the already de-duplicated list
                "skills": user_skills 
            }
        }

def get_users(db: Session):
    # This query retrieves all user data and skills
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
        # Only append the skill if it's not already in the list for this user (De-duplication in API output)
        if row.skill_name and row.skill_name not in users_dict[row.user_id]["skills"]:
            users_dict[row.user_id]["skills"].append(row.skill_name)

    return list(users_dict.values())