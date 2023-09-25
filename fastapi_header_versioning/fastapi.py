from collections.abc import Callable, Sequence
from typing import Any, Optional, Union

from fastapi import Depends, FastAPI
from fastapi.applications import AppType
from fastapi.datastructures import Default
from fastapi.routing import APIRoute
from fastapi.utils import generate_unique_id
from starlette.responses import JSONResponse, Response
from starlette.routing import BaseRoute
from starlette.types import Lifespan, Receive, Scope, Send

from .routing import HeaderVersionedAPIRouter


class CustomHeaderVersionMiddleware:
    def __init__(
        self,
        app: FastAPI,
        version_header: str,
    ) -> None:
        self.app = app
        self.version_header = version_header.encode()

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] in ("http", "websocket"):
            headers: dict[bytes, bytes] = dict(scope["headers"])
            scope["requested_version"] = None
            if self.version_header in headers:
                scope["requested_version"] = headers[self.version_header].decode()

        return await self.app(scope, receive, send)


class HeaderRoutingFastAPI(FastAPI):
    def __init__(
        self,
        version_header: str,
        routes: Optional[list[BaseRoute]] = None,
        dependencies: Optional[Sequence[Depends]] = None,
        default_response_class: type[Response] = Default(JSONResponse),
        on_startup: Optional[Sequence[Callable[[], Any]]] = None,
        on_shutdown: Optional[Sequence[Callable[[], Any]]] = None,
        lifespan: Optional[Lifespan[AppType]] = None,
        responses: Optional[dict[Union[int, str], dict[str, Any]]] = None,
        callbacks: Optional[list[BaseRoute]] = None,
        deprecated: Optional[bool] = None,
        include_in_schema: bool = True,
        generate_unique_id_function: Callable[[APIRoute], str] = Default(
            generate_unique_id,
        ),
        *args: Any,
        **kwargs: Any,
    ):
        super().__init__(
            *args,
            routes=routes,
            dependencies=dependencies,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            lifespan=lifespan,
            default_response_class=default_response_class,
            callbacks=callbacks,
            deprecated=deprecated,
            include_in_schema=include_in_schema,
            responses=responses,
            generate_unique_id_function=generate_unique_id_function,
            **kwargs,
        )
        self.router = HeaderVersionedAPIRouter(
            routes=routes,
            dependency_overrides_provider=self,
            on_startup=on_startup,
            on_shutdown=on_shutdown,
            lifespan=lifespan,
            default_response_class=default_response_class,
            dependencies=dependencies,
            callbacks=callbacks,
            deprecated=deprecated,
            include_in_schema=include_in_schema,
            responses=responses,
            generate_unique_id_function=generate_unique_id_function,
        )
        self.add_middleware(
            CustomHeaderVersionMiddleware,
            version_header=version_header,
        )
