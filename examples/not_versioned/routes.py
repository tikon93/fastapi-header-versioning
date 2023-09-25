from fastapi.routing import APIRouter

router = APIRouter()


@router.get("/hell")
async def greeting():
    return {"greeting": f"Hi! It's not versioned route."}

