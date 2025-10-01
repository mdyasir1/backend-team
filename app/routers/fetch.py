from fastapi import APIRouter, Depends, HTTPException
from app import crud 
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from app.database import get_db
from app.models import User
from app.schemas import SubmissionResponse
from typing import List

router = APIRouter()

@router.get("/submissions", response_model=List[SubmissionResponse], status_code=200)
@router.get("/submissions", response_model=list[SubmissionResponse], status_code=200)
async def get_submissions(db: AsyncSession = Depends(get_db)):
    try:
        return await crud.get_submissions(db)
    except HTTPException as e:
        raise e # Re-raise if crud returns HTTPException
    except Exception as e:
        # This is where a generic 500 comes from if you don't raise the error detail
        raise HTTPException(status_code=500, detail=f"Internal server error during fetch: {str(e)}")
