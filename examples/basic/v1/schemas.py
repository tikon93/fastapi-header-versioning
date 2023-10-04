import uuid

from pydantic import BaseModel


class Item(BaseModel):
    name: str
    description: str


class ItemResponse(Item):
    id: uuid.UUID


class ItemPatch(BaseModel):
    name: str | None = None
    description: str | None = None


class GetResponse(BaseModel):
    dependency_parameters: dict
    query_parameter: str
    id: uuid.UUID
    version: str
