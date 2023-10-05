import uvicorn

from examples.basic.no_version.routes import router
from examples.basic.v1.routes import router as router_v1
from examples.basic.v2.routes import router as router_v2
from fastapi_header_versioning import HeaderRoutingFastAPI
from fastapi_header_versioning.openapi import doc_generation

app = HeaderRoutingFastAPI(version_header="x-version", title="Versioned app")
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
