from collections.abc import Callable, Sequence
from enum import Enum
from functools import cache
from typing import (
    Any,
    Optional,
    TypeVar,
    Union,
)

from fastapi import APIRouter, params
from fastapi.datastructures import Default
from fastapi.routing import APIRoute
from fastapi.types import DecoratedCallable
from fastapi.utils import (
    generate_unique_id,
)
from starlette.datastructures import URL
from starlette.exceptions import HTTPException
from starlette.responses import JSONResponse, PlainTextResponse, RedirectResponse, Response
from starlette.routing import (
    BaseRoute,
    Match,
)
from starlette.types import Receive, Scope, Send

_T = TypeVar("_T")


def same_definition_as_in(t: _T) -> Callable[[Callable], _T]:
    def decorator(f: Callable) -> _T:
        return f  # pyright: ignore[reportGeneralTypeIssues]

    return decorator


class HeaderVersionedAPIRoute(APIRoute):
    api_version = None

    def is_version_matching(self, scope: Scope) -> bool:
        requested_version = scope["requested_version"]
        return self.api_version == requested_version

    def matches(self, scope: Scope) -> tuple[Match, Scope]:
        match, child_scope = super().matches(scope)

        if match == Match.NONE or match == Match.PARTIAL:
            return match, child_scope

        if self.is_version_matching(scope):
            return Match.FULL, child_scope

        return Match.NONE, child_scope


@cache
def specific_version_api_route(
    version: str,
    route_class: type[APIRoute] = APIRoute,
) -> type[APIRoute]:
    class SpecificVersionAPIRoute(HeaderVersionedAPIRoute, route_class):
        api_version = version

    return SpecificVersionAPIRoute


async def handle_non_existing_version(scope: Scope, receive: Receive, send: Send) -> None:
    if "app" in scope:
        raise HTTPException(
            406,
            f"Requested version {scope['requested_version']} does not exist. ",
        )

    response = PlainTextResponse("Not Acceptable", status_code=406)  # pragma: no cover
    await response(scope, receive, send)  # pragma: no cover


class HeaderVersionedAPIRouter(APIRouter):
    def __init__(
        self,
        default_version: str | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        self.default_version: str | None = default_version
        self._context_version: str | None = None
        self.registered_versions: set[str | None] = set()
        self.registered_versions.add(self.default_version)
        super().__init__(*args, **kwargs)

    def version(
        self,
        api_version: str,
    ) -> Callable[[DecoratedCallable], DecoratedCallable]:
        self.registered_versions.add(api_version)

        def decorator(func: DecoratedCallable) -> DecoratedCallable:
            func.__endpoint_api_version__ = api_version
            return func

        return decorator

    @same_definition_as_in(APIRouter.add_api_route)
    def add_api_route(
        self,
        path: str,
        endpoint: Callable[..., Any],
        *,
        route_class_override: type[APIRoute] | None = None,
        **kwargs: Any,
    ):
        if route_class_override:
            # called from include_router or similar functions - we are re-generating routes

            # don't override route_class for already versioned routes
            if not issubclass(route_class_override, HeaderVersionedAPIRoute) and self._context_version:
                # need to wrap original route class with HeaderVersionedAPIRoute
                # currently including routes from unversioned router with some externally defined version
                route_class_override = specific_version_api_route(
                    self._context_version,
                    route_class_override,
                )
        else:
            # called from decorator-based routes declaration. extract __endpoint_api_version__ if set and generate
            # proper route
            if endpoint_version := getattr(endpoint, "__endpoint_api_version__", None):
                route_class_override = specific_version_api_route(endpoint_version, APIRoute)
            else:
                # wrap with default version
                route_class_override = specific_version_api_route(self.default_version, APIRoute)

        super().add_api_route(path, endpoint, route_class_override=route_class_override, **kwargs)

    def include_router(
        self,
        router: "APIRouter",
        *,
        prefix: str = "",
        version: str | None = None,
        tags: Optional[list[Union[str, Enum]]] = None,
        dependencies: Optional[Sequence[params.Depends]] = None,
        default_response_class: type[Response] = Default(JSONResponse),
        responses: Optional[dict[Union[int, str], dict[str, Any]]] = None,
        callbacks: Optional[list[BaseRoute]] = None,
        deprecated: Optional[bool] = None,
        include_in_schema: bool = True,
        generate_unique_id_function: Callable[[APIRoute], str] = Default(
            generate_unique_id,
        ),
    ) -> None:
        """
        if 'version' provided - include all the unversioned routes with this version. May be used to wrap existing
        routers with desired version.
        """
        self._context_version = version
        self.registered_versions.add(version)
        super().include_router(
            router=router,
            prefix=prefix,
            tags=tags,
            dependencies=dependencies,
            default_response_class=default_response_class,
            responses=responses,
            callbacks=callbacks,
            deprecated=deprecated,
            include_in_schema=include_in_schema,
            generate_unique_id_function=generate_unique_id_function,
        )
        if isinstance(router, HeaderVersionedAPIRouter):
            self.registered_versions.update(router.registered_versions)

        self._context_version = None

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:  # noqa: C901
        """
        Mostly a duplicate of FastAPI implementation, but with ability to handle partially matched versions.
        A lot of no-covers as there are a lot of edge cases handled exactly as fastapi does
        """
        assert scope["type"] in ("http", "websocket", "lifespan")  # noqa: S101

        if "router" not in scope:  # pragma: no cover
            scope["router"] = self

        if scope["type"] == "lifespan":  # pragma: no cover
            await self.lifespan(scope, receive, send)
            return

        partial = None
        partial_scope = None
        requested_version = scope.get("requested_version")

        if requested_version is not None and requested_version not in self.registered_versions:
            # there are no such route with exactly the same version - just use the closest, but last version.
            # eg - request passed with version header value "10.10.1", and app has only "9.0.0" and "11.0.0".
            # we'll fallback to "9.0.0". It makes sense if there are many different services with independent
            # release cycles. Thus, one service may release 100 different API versions and another - just 2. Clients
            # will be able to use same header for requests to both services, not caring a lot about which versions are
            # supported in each service.
            suitable_versions = []
            for version in self.registered_versions:
                if version is not None and version < requested_version:
                    suitable_versions.append(version)

            if not suitable_versions:
                # this implementation will trigger 406 even on not versioned route if provided version is not registered
                # however, it covers more real-world scenarios. proper distinguishing between 404 in case of not
                # versioned route and 406 with not found version requires deep dive into starlette's Mount (used for
                # doc generation) implementation which seems to be weird in case of further match processing
                await handle_non_existing_version(scope, receive, send)
                # it's not really executed as we'll return from function above, but for code readability it's better
                # to have it
                return  # pragma: no cover
            version_to_use = max(suitable_versions)
            scope["requested_version"] = version_to_use
            # maybe we can generate more narrow set of routes at this point, but it's possible to optimize it later

        for route in self.routes:
            # Determine if any route matches the incoming scope,
            # and hand over to the matching route if found.
            match, child_scope = route.matches(scope)
            if match == Match.FULL:
                scope.update(child_scope)
                await route.handle(scope, receive, send)
                return  # pragma: no cover

            if match == Match.PARTIAL and partial is None:
                partial = route
                partial_scope = child_scope

        if partial is not None:
            # Handle partial matches. These are cases where an endpoint is
            # able to handle the request, but is not a preferred option.
            # We use this in particular to deal with "405 Method Not Allowed".
            scope.update(partial_scope)  # pyright: ignore[reportGeneralTypeIssues]
            await partial.handle(scope, receive, send)
            return  # pragma: no cover

        if scope["type"] == "http" and self.redirect_slashes and scope["path"] != "/":
            redirect_scope = dict(scope)
            if scope["path"].endswith("/"):
                redirect_scope["path"] = redirect_scope["path"].rstrip("/")
            else:
                redirect_scope["path"] = redirect_scope["path"] + "/"

            for route in self.routes:
                match, child_scope = route.matches(redirect_scope)
                if match != Match.NONE:
                    redirect_url = URL(scope=redirect_scope)
                    response = RedirectResponse(url=str(redirect_url))
                    await response(scope, receive, send)
                    return

        await self.default(scope, receive, send)
