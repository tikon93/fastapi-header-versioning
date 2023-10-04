import uvicorn

from examples.router_level_versions.not_versioned.routes import router
from examples.router_level_versions.v1.routes import router as router_v1
from examples.router_level_versions.v2.routes import router as router_v2
from fastapi_header_versioning import HeaderRoutingFastAPI
from fastapi_header_versioning.openapi import doc_generation
from fastapi_header_versioning.routing import HeaderVersionedAPIRouter

app = HeaderRoutingFastAPI(version_header="x-version", title="Versioned app")
router_override = HeaderVersionedAPIRouter(default_version="foo")

router_override.include_router(router)


app.include_router(router_override)
app.include_router(router_v1)
app.include_router(router_v2)
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
