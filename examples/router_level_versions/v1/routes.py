import uuid

from fastapi import Depends, Response, status

from fastapi_header_versioning import HeaderVersionedAPIRouter

from ..commons import get_version
from .schemas import GetResponse, Item, ItemResponse

router = HeaderVersionedAPIRouter(default_version="1")


async def get_parameters(skip: int = 0, limit: int = 100):
    return {"skip": skip, "limit": limit}


@router.get("/item/{item_id}", response_model=GetResponse)
async def get_item(
    item_id: uuid.UUID,
    query_parameter: str,
    dependency_parameters: dict = Depends(get_parameters),
    version: str = Depends(get_version),
):
    return {
        "query_parameter": query_parameter,
        "id": item_id,
        "dependency_parameters": dependency_parameters,
        "version": version,
    }


@router.post("/item", response_model=ItemResponse)
async def create_item(item: Item):
    created_item = item.dict()
    created_item["id"] = uuid.uuid4()
    return created_item


@router.patch("/item/{item_id}", response_model=ItemResponse)
async def update_item(item_id: uuid.UUID, item: Item):
    return {"id": item_id, "name": "base_name", "description": "base_description"}.update(
        item.dict(exclude_none=True),
    )


@router.put("/item/{item_id}", response_model=ItemResponse)
async def replace_item(item_id: uuid.UUID, item: Item):
    replaced_item = item.dict()
    replaced_item["id"] = item_id

    return replaced_item


@router.delete("/item/{item_id}")
async def delete_item(item_id: uuid.UUID):
    return Response(status_code=status.HTTP_204_NO_CONTENT)
