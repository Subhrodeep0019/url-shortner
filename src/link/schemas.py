from pydantic import BaseModel, HttpUrl, Field
from uuid import UUID
from datetime import datetime

class LinkCreateModel(BaseModel):
    long_url: HttpUrl
    custom_alias: str | None = Field(
                                   default=None,
                                   min_length=4,
                                   max_length=15,
                                   pattern=r"^[a-zA-Z0-9]+$",
                               )
    expires_at: datetime | None = None

class LinkResponseModel(BaseModel):
    uid: UUID
    short_url: str
    long_url: HttpUrl
    created_at: datetime
    expires_at: datetime | None = None
