import uuid

from pydantic import BaseModel


class Item(BaseModel):
    new_field_for_name: str
    description: str


class ItemResponse(Item):
    item_id: uuid.UUID


class ItemPatch(BaseModel):
    new_field_for_name: str | None = None
    description: str | None = None


class GetResponse(BaseModel):
    commons: str
    new_query_parameter: str
    item_id: uuid.UUID
    version: str
