from sqlalchemy.orm import Session
from sqlalchemy import text
from app import schemas
from typing import Dict, Any, List

def create_user(db: Session, user: schemas.UserCreate) -> Dict[str, Any]:
    """
    Creates a new user. If an existing email is submitted, it rejects the submission 
    and returns a conflict status, preventing any updates.
    """
    
    # 1. Check for existing user by email
    existing_user_query = text("""
        SELECT user_id, username, email, location FROM users WHERE email = :email;
    """)
    existing_user_result = db.execute(existing_user_query, {"email": user.email}).fetchone()

    if existing_user_result:
        # ** Existing User Found: Block Submission and Prevent Updates **
        db.rollback() # Ensure no transaction is open
        return {
            "status_code": 409, # Conflict status for the API to handle
            "message": "email already exsits"
        }

    # Helper function to get skill_id (only used for new user creation below)
    def get_or_create_skill(skill_name: str) -> int:
        # Insert skill (if not exists, ignore)
        skill_result = db.execute(text("""
            INSERT INTO skills (skill_name)
            VALUES (:skill_name)
            ON CONFLICT (skill_name) DO UPDATE SET skill_name = EXCLUDED.skill_name
            RETURNING skill_id;
        """), {"skill_name": skill_name})
        return skill_result.fetchone().skill_id


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
        # This catch block is a safety net for a race condition or DB unique constraint error.
        if "duplicate key value violates unique constraint" in str(e):
             return {
                "status_code": 409, 
                "message": "user already exsits"
            }
        raise e


    # 3. Insert skills and map to user
    for skill in user.skills:
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
            "skills": user.skills
        }
    }

def get_users(db: Session):
    # This function remains unchanged as it simply retrieves all users
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
        if row.skill_name:
            users_dict[row.user_id]["skills"].append(row.skill_name)

    return list(users_dict.values())