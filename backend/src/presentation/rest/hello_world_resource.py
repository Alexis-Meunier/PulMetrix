from fastapi import APIRouter

router = APIRouter()


@router.get("/hello/", tags=["hello_world_tag"])
async def hello_world():
    return {"message": "Hello World"}
