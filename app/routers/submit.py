from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.schemas import SubmissionCreate, SubmissionResponse
from app.database import get_db
from app import crud

router = APIRouter()

@router.post("/submit-form", response_model=SubmissionResponse, status_code=status.HTTP_201_CREATED)
async def submit_form(payload: SubmissionCreate, db: AsyncSession = Depends(get_db)):
    """
    Person 3: Store validated form submission into Postgres
    """
    return await crud.create_submission(db, payload)
