from pydantic import BaseModel, HttpUrl
from uuid import UUID
from datetime import datetime

class LinkCreateModel(BaseModel):
    long_url: HttpUrl
    custom_alias: str | None = None
    expires_at: datetime | None = None

class LinkResponseModel(BaseModel):
    uid: UUID
    short_url: str
    long_url: HttpUrl
    created_at: datetime
    expires_at: datetime | None = None
