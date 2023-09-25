from .fastapi import HeaderRoutingFastApi
from typing import Dict, List
from fastapi.routing import APIRoute
from .routing import HeaderVersionedAPIRoute
from collections import defaultdict
from starlette.routing import BaseRoute
from fastapi import FastAPI


def get_version_from_route(route: APIRoute) -> str | None:
    if isinstance(route, HeaderVersionedAPIRoute):
        return route.endpoint_version or None

    return None


def doc_generation(
    app: HeaderRoutingFastApi,
) -> HeaderRoutingFastApi:
    parent_app = app
    version_route_mapping: Dict[str | None, List[APIRoute]] = defaultdict(list)

    for route in app.routes:
        version = get_version_from_route(route)
        version_route_mapping[version].append(route)


    versions = version_route_mapping.keys()
    for version in versions:
        unique_routes = {}
        version_description = version if version is not None else "Not versioned"
        versioned_app = FastAPI(
            title=app.title,
            description=version_description + " " +app.description,
        )
        for route in version_route_mapping[version]:
            for method in route.methods:
                unique_routes[route.path + "|" + method] = route

        versioned_app.router.routes.extend(unique_routes.values())

        prefix = f"/version_{version}"
        if version is None:
            prefix = "/"
        parent_app.mount(prefix, versioned_app)

    return parent_app
