from fastapi import APIRouter

router = APIRouter()


@router.get("/")
def read_root():
    return {"message": "Welcome to FastAPI Backend"}


@router.get("/api/health")
def health_check():
    return {"status": "healthy"}