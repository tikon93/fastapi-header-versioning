import uuid

from fastapi import APIRouter, Depends, Response, status

from .schemas import GetResponse, Item, ItemResponse

router = APIRouter()


async def get_parameters(offset: int = 0, limit: int = 100):
    # parameters set differs from v1
    return {"offset": offset, "limit": limit}


@router.get("/item/{item_id}", response_model=GetResponse)
async def get_item(
    item_id: uuid.UUID,
    new_query_parameter: str,
    dependency_parameters: dict = Depends(get_parameters),
):
    return {
        "new_query_parameter": new_query_parameter,
        "id": item_id,
        "dependency_parameters": dependency_parameters,
    }


@router.post("/item", response_model=ItemResponse)
async def create_item(item: Item):
    created_item = item.dict()
    created_item["id"] = uuid.uuid4()
    return created_item


@router.patch("/item/{item_id}", response_model=ItemResponse)
async def update_item(item_id: uuid.UUID, item: Item):
    return {"id": item_id, "new_field_for_name": "base_name", "description": "base_description"}.update(
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
