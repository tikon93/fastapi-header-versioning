import uuid

from fastapi import Depends, Response, status

from examples.commons import get_version
from fastapi_header_versioning import HeaderVersionedAPIRouter

from .schemas import GetResponse, Item, ItemResponse

router = HeaderVersionedAPIRouter()


async def get_parameters(skip: int = 0, limit: int = 100):
    return {"skip": skip, "limit": limit}


@router.get("/item/{item_id}", response_model=GetResponse)
@router.version("1")
async def get_item(
    item_id: uuid.UUID,
    query_parameter: str,
    dependency_parameters: dict = Depends(get_parameters),
    version: str = Depends(get_version),
):
    return {
        "query_parameter": query_parameter,
        "item_id": item_id,
        "dependency_parameters": dependency_parameters,
        "version": version,
    }


@router.post("/item", response_model=ItemResponse)
@router.version("1")
async def create_item(item: Item, version: str = Depends(get_version)):
    created_item = item.model_dump()
    created_item["id"] = uuid.uuid4()
    return {"item": created_item, "version": version}


@router.patch("/item/{item_id}", response_model=ItemResponse)
@router.version("1")
async def update_item(item_id: uuid.UUID, item: Item, version: str = Depends(get_version)):
    updated_item = {"id": item_id, "name": "base_name", "description": "base_description"}.update(
        item.model_dump(exclude_none=True),
    )
    return {
        "item": updated_item,
        "version": version,
    }


@router.put("/item/{item_id}", response_model=ItemResponse)
@router.version("1")
async def replace_item(item_id: uuid.UUID, item: Item, version: str = Depends(get_version)):
    replaced_item = item.model_dump()
    replaced_item["id"] = item_id
    return {"item": item, "version": version}


@router.delete("/item/{item_id}")
@router.version("1")
async def delete_item(item_id: uuid.UUID, version: str = Depends(get_version)):
    return Response(status_code=status.HTTP_204_NO_CONTENT)
