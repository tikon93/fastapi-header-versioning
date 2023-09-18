import uvicorn
from fastapi_hbr import HeaderBasedRoutingFastApi, HeaderVersionedAPIRouter, CustomHeaderVersionMiddleware


GREETINGS_V1 = "Hello"
GREETINGS_V2 = "It's me"
GREETINGS_V3 = "I was wondering if after all these years you'd like to meet"
GREETINGS_LATEST = "Hello, can you hear me?"

router = HeaderVersionedAPIRouter()


@router.get("/hello")
@router.version("1")
async def hello_v1() -> dict:
    return {"greetings": GREETINGS_V1}


@router.get("/hello")
@router.version("2")
async def hello_v2() -> dict:
    return {"greetings": GREETINGS_V2}


@router.get("/hello")
@router.version("3")
async def hello_v3() -> dict:
    return {"greetings": GREETINGS_V3}


@router.get("/hello")
@router.version("latest")
async def hello_latest() -> dict:
    return {"greetings": GREETINGS_LATEST}


app = HeaderBasedRoutingFastApi(title="Versioned app")
app.add_middleware(
    CustomHeaderVersionMiddleware, version_header="x-version",
)
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
