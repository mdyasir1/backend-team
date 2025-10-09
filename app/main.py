from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from app import schemas, crud
from app.database import SessionLocal
import uvicorn
# Initialize DB (recreate tables each run for testing)
# init_db()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Dependency: DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.post("/submit-form", response_model=schemas.SubmissionStatus)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    try:
        # crud.create_user returns a dict with status_code and message
        result = crud.create_user(db, user)
        
        if result.get("status_code") == 409: 
             raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=result.get("message")
            )
        
        # New or updated user
        return {
            "message": result.get("message"),
            "user_data": result.get("user_data")
        }
        
    except HTTPException as e:
        raise e
    except Exception as e:
        db.rollback() 
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
            detail=f"An error occurred during submission: {str(e)}"
        )

@app.get("/submissions", response_model=list[schemas.UserResponse])
def read_users(db: Session = Depends(get_db)):
    return crud.get_users(db)

# if __name__ == '__main__':
#     uvicorn.run('main:app',host='0.0.0.0' , port=8000, reload=True)