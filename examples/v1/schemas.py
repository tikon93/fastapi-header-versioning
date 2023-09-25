import uuid

from pydantic import BaseModel


class Item(BaseModel):
    name: str
    description: str


class ItemResponse(Item):
    item_id: uuid.UUID


class ItemPatch(BaseModel):
    name: str | None = None
    description: str | None = None


class GetResponse(BaseModel):
    dependency_parameters: str
    query_parameter: str
    item_id: uuid.UUID
    version: str
