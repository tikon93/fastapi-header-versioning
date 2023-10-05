import uvicorn

from examples.unversioned_routers_wrapping.no_version.routes import router
from examples.unversioned_routers_wrapping.v1.routes import router as router_v1
from examples.unversioned_routers_wrapping.v2.routes import router as router_v2
from fastapi_header_versioning import HeaderRoutingFastAPI, HeaderVersionedAPIRouter
from fastapi_header_versioning.openapi import doc_generation

app = HeaderRoutingFastAPI(version_header="x-version", title="Versioned app")

root_router = HeaderVersionedAPIRouter()
root_router.include_router(router_v1, version="1")
root_router.include_router(router_v2, version="2")
root_router.include_router(router)

app.include_router(root_router)
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
