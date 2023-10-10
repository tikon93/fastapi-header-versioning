from collections import defaultdict

from fastapi import FastAPI
from fastapi.routing import APIRoute
from starlette.routing import BaseRoute

from .fastapi import HeaderRoutingFastAPI
from .routing import HeaderVersionedAPIRoute


def get_version_from_route(route: BaseRoute) -> str | None:
    if isinstance(route, HeaderVersionedAPIRoute):
        return route.api_version or None

    return None


def doc_generation(
    app: HeaderRoutingFastAPI,
) -> HeaderRoutingFastAPI:
    parent_app = app
    version_route_mapping: dict[str | None, list[BaseRoute]] = defaultdict(list)

    for route in app.routes:
        version = get_version_from_route(route)  # pyright: ignore[reportGeneralTypeIssues]
        version_route_mapping[version].append(route)  # pyright: ignore[reportGeneralTypeIssues]

    versions = version_route_mapping.keys()
    for version in versions:
        unique_routes = {}
        version_description = version if version is not None else "Not versioned"
        versioned_app = FastAPI(
            title=app.title,
            description=version_description + " " + app.description,
        )
        for route in version_route_mapping[version]:
            if isinstance(route, APIRoute):
                for method in route.methods:
                    unique_routes[route.path + "|" + method] = route

            # TODO: support websocket routes

        versioned_app.router.routes.extend(unique_routes.values())

        prefix = f"/version_{version}"
        if version is None:
            prefix = "/no_version"
        parent_app.mount(prefix, versioned_app)

    return parent_app
