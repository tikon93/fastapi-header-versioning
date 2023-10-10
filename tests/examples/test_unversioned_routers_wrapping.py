import uuid

import pytest
from fastapi.testclient import TestClient

from examples.unversioned_routers_wrapping.app import app


@pytest.fixture()
def client() -> TestClient:
    return TestClient(
        app,
    )


@pytest.fixture()
def item_id() -> str:
    return str(uuid.uuid4())


async def test__versioned_route__exact_version_matching__should_use_correct_version(client: TestClient, item_id: str):
    result = client.get(f"/item/{item_id}?query_parameter=foo", headers={"x-version": "1"})
    assert result.status_code == 200
    assert result.json() == {
        "query_parameter": "foo",
        "id": item_id,
        "dependency_parameters": {
            "skip": 0,
            "limit": 100,
        },
        "version": "1",
    }

    result = client.get(f"/item/{item_id}?new_query_parameter=foo", headers={"x-version": "2"})
    assert result.status_code == 200
    assert result.json() == {
        "new_query_parameter": "foo",
        "id": item_id,
        "dependency_parameters": {
            "offset": 0,
            "limit": 100,
        },
    }


@pytest.mark.parametrize("headers", [{"x-version": "1"}, {"x-version": "3"}, {}])
async def test__route_without_version__any_version_header__should_use_correct_route(client: TestClient, headers):
    result = client.get("/hello", headers=headers)
    assert result.status_code == 200
    assert result.json() == {"greeting": "Hi! It's not versioned route."}


async def test__versioned_route__not_exact_version__should_use_correct_route(client: TestClient, item_id: str):
    result = client.get(f"/item/{item_id}?query_parameter=foo", headers={"x-version": "1.5"})
    assert result.status_code == 200
    assert result.json() == {
        "query_parameter": "foo",
        "id": item_id,
        "dependency_parameters": {
            "skip": 0,
            "limit": 100,
        },
        "version": "1.5",
    }

    result = client.get(f"/item/{item_id}?new_query_parameter=foo", headers={"x-version": "3"})
    assert result.status_code == 200
    assert result.json() == {
        "new_query_parameter": "foo",
        "id": item_id,
        "dependency_parameters": {
            "offset": 0,
            "limit": 100,
        },
    }


async def test__versioned_route__impossible_to_pick_version__should_return_406(client: TestClient, item_id):
    result = client.get(f"/item/{item_id}?query_parameter=foo", headers={"x-version": "0"})
    assert result.status_code == 406


async def test__versioned_route__not_existing_path__should_return_404(client: TestClient):
    result = client.get(f"/item/{item_id}/foo?new_query_parameter=foo", headers={"x-version": "2"})
    assert result.status_code == 404


@pytest.mark.parametrize("path", ["/hello", "/item/foo"])
async def test__any_route__not_existing_method__should_return_405(client: TestClient, path: str):
    result = client.head(path, headers={"x-version": "2"})
    assert result.status_code == 405
