from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import submit, fetch
from app.database import Base, engine

app = FastAPI(title="Form Submission Backend")

# Allow frontend requests
origins = ["http://localhost:3000"]  # Update with actual frontend deployment URL
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Auto-create DB tables
@app.on_event("startup")
async def startup_event():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Include routers
app.include_router(submit.router)
app.include_router(fetch.router)
