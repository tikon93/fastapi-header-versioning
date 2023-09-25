from collections.abc import Callable
from typing import Any, TypeVar

from fastapi import APIRouter
from fastapi.routing import APIRoute
from fastapi.types import DecoratedCallable
from starlette.datastructures import URL
from starlette.exceptions import HTTPException
from starlette.responses import PlainTextResponse, RedirectResponse
from starlette.routing import Match
from starlette.types import Receive, Scope, Send

_T = TypeVar("_T")


def same_definition_as_in(t: _T) -> Callable[[Callable], _T]:
    def decorator(f: Callable) -> _T:
        return f  # pyright: ignore[reportGeneralTypeIssues]

    return decorator


async def handle_non_existing_version(scope: Scope, receive: Receive, send: Send) -> None:
    if "app" in scope:
        raise HTTPException(
            406,
            f"Requested version {scope['requested_version']} does not exist. ",
        )

    response = PlainTextResponse("Not Acceptable", status_code=406)
    await response(scope, receive, send)


class HeaderVersionedAPIRoute(APIRoute):
    @property
    def endpoint_version(self) -> str | None:
        # get version declared by decorator or fallback to None in case if decorator was not used
        version = getattr(self.endpoint, "__api_version__", None)
        if version is None:
            return None

        return str(version)

    def is_version_matching(self, scope: Scope) -> bool:
        requested_version = scope["requested_version"]
        return self.endpoint_version == requested_version

    def matches(self, scope: Scope) -> tuple[Match, Scope]:
        match, child_scope = super().matches(scope)

        if match == Match.NONE or match == Match.PARTIAL:
            return match, child_scope

        if self.is_version_matching(scope):
            return Match.FULL, child_scope

        return Match.PARTIAL, child_scope

    async def handle(self, scope: Scope, receive: Receive, send: Send) -> None:
        if not self.is_version_matching(scope):
            await handle_non_existing_version(scope, receive, send)
            return
        await super().handle(scope, receive, send)


class HeaderVersionedAPIRouter(APIRouter):
    def __init__(
        self,
        *args: Any,
        route_class: type[HeaderVersionedAPIRoute] = HeaderVersionedAPIRoute,
        **kwargs: Any,
    ) -> None:
        self.registered_versions: set[str] = set()
        super().__init__(*args, route_class=route_class, **kwargs)

    def version(
        self,
        api_version: str,
    ) -> Callable[[DecoratedCallable], DecoratedCallable]:
        self.registered_versions.add(api_version)

        def decorator(func: DecoratedCallable) -> DecoratedCallable:
            func.__api_version__ = api_version
            return func

        decorator.__is_versioned__ = True
        return decorator

    @same_definition_as_in(APIRouter.include_router)
    def include_router(
        self,
        router: "APIRouter",
        *args: Any,
        **kwargs: Any,
    ) -> None:
        super().include_router(router, *args, **kwargs)
        if isinstance(router, HeaderVersionedAPIRouter):
            self.registered_versions.update(router.registered_versions)

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """
        Mostly a duplicate of FastAPI implementation, but with ability to handle partially matched versions.
        """
        assert scope["type"] in ("http", "websocket", "lifespan")  # noqa: S101

        if "router" not in scope:
            scope["router"] = self

        if scope["type"] == "lifespan":
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

            suitable_versions = [version for version in self.registered_versions if version < requested_version]
            if not suitable_versions:
                await handle_non_existing_version(scope, receive, send)
                return
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
                return

            if match == Match.PARTIAL and partial is None:
                partial = route
                partial_scope = child_scope

        if partial is not None:
            # Handle partial matches. These are cases where an endpoint is
            # able to handle the request, but is not a preferred option.
            # We use this in particular to deal with "405 Method Not Allowed".
            scope.update(partial_scope)  # pyright: ignore[reportGeneralTypeIssues]
            await partial.handle(scope, receive, send)
            return

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
