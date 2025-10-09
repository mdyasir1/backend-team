from sqlalchemy.orm import Session
from sqlalchemy import text
import schemas

def create_user(db: Session, user: schemas.UserCreate):
    # Insert user
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

    # Insert skills if not exist, then map to user
    for skill in user.skills:
        # Insert skill (if not exists, ignore)
        skill_result = db.execute(text("""
            INSERT INTO skills (skill_name)
            VALUES (:skill_name)
            ON CONFLICT (skill_name) DO UPDATE SET skill_name = EXCLUDED.skill_name
            RETURNING skill_id;
        """), {"skill_name": skill})
        skill_id = skill_result.fetchone().skill_id

        # Insert mapping into user_skills
        db.execute(text("""
            INSERT INTO user_skills (user_id, skill_id)
            VALUES (:user_id, :skill_id)
            ON CONFLICT (user_id, skill_id) DO NOTHING;
        """), {"user_id": user_id, "skill_id": skill_id})

    db.commit()

    return {
        "user_id": db_user.user_id,
        "username": db_user.username,
        "email": db_user.email,
        "location": db_user.location,
        "skills": user.skills
    }

def get_users(db: Session):
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
