import uvicorn
from typing import Dict
from fastapi_header_versioning import HeaderBasedRoutingFastApi, HeaderVersionedAPIRouter


router = HeaderVersionedAPIRouter()


@router.get("/hello")
@router.version("1")
async def hello_v1() -> Dict:
    return {"greetings": "V1 hello!"}


@router.get("/hello")
@router.version("2")
async def hello_v2() -> Dict:
    return {"greetings": "V2 hello!"}


@router.get("/hello")
@router.version("3")
async def hello_v3() -> Dict:
    return {"greetings": "V3 hello!"}


@router.get("/hello")
@router.version("some_other_string")
async def hello_latest() -> Dict:
    return {"greetings": "Some other greeting"}


@router.get("/hello_not_versioned")
async def hello_latest() -> Dict:
    return {"greetings": "Not versioned greeting."}


app = HeaderBasedRoutingFastApi(version_header="x-version", title="Versioned app")
app.include_router(router)


uvicorn.Config(
    app=app,
    proxy_headers=True,
    access_log=False,
)

if __name__ == "__main__":
    uvicorn.run(
        app=app,
        port=9999,
        reload=False,
    )
