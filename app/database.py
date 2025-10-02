from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://postgres:safiyarafi111@user-skills-db.cxc8uamw6vkx.ap-south-1.rds.amazonaws.com:5432/postgres"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

def init_db():
    with engine.connect() as conn:
        conn.execute(text("DROP TABLE IF EXISTS user_skills;"))
        conn.execute(text("DROP TABLE IF EXISTS skills;"))
        conn.execute(text("DROP TABLE IF EXISTS users;"))

        conn.execute(text("""
            CREATE TABLE users (
                user_id SERIAL PRIMARY KEY,
                username VARCHAR(100) NOT NULL,
                email VARCHAR(100) NOT NULL UNIQUE,
                location VARCHAR(100)
            );
        """))

        conn.execute(text("""
            CREATE TABLE skills (
                skill_id SERIAL PRIMARY KEY,
                skill_name VARCHAR(100) NOT NULL UNIQUE
            );
        """))

        conn.execute(text("""
            CREATE TABLE user_skills (
                user_skill_id SERIAL PRIMARY KEY,
                user_id INT NOT NULL,
                skill_id INT NOT NULL,
                CONSTRAINT fk_user FOREIGN KEY(user_id) REFERENCES users(user_id) ON DELETE CASCADE,
                CONSTRAINT fk_skill FOREIGN KEY(skill_id) REFERENCES skills(skill_id) ON DELETE CASCADE,
                CONSTRAINT unique_user_skill UNIQUE(user_id, skill_id)
            );
        """))

        conn.commit()
