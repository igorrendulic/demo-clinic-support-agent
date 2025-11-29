from fastapi import APIRouter

root_router = APIRouter()

@root_router.get("/")
async def index():
    return {"message": "Appointment Scheduler Demo API v1.0.0!"}