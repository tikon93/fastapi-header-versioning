import uvicorn

from examples.v1.routes import router as router_v1
from examples.v2.routes import router as router_v2
from examples.not_versioned.routes import router
from fastapi_header_versioning import HeaderRoutingFastApi
from fastapi_header_versioning.openapi import doc_generation

app = HeaderRoutingFastApi(version_header="x-version", title="Versioned app", )
app.include_router(router_v1)
app.include_router(router_v2)
app.include_router(router)
app = doc_generation(app)

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
