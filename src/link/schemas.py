from pydantic import BaseModel, HttpUrl, Field, field_validator
from uuid import UUID
from datetime import datetime, timezone

class LinkCreateModel(BaseModel):
    long_url: HttpUrl
    custom_alias: str | None = Field(
                                   default=None,
                                   min_length=4,
                                   max_length=15,
                                   pattern=r"^[a-zA-Z0-9]+$",
                               )
    expires_at: datetime | None = None

    @field_validator("expires_at")
    @classmethod
    def normalize_expiry(cls, value: datetime | None) -> datetime | None:
        if value is None:
            return None

        # convert to UTC & then drop the zone
        if value.tzinfo is not None:
            value = value.astimezone(timezone.utc).replace(tzinfo=None)

        now = datetime.now(timezone.utc).replace(tzinfo=None)
        if value <= now:
            raise ValueError("expires_at must be in the future")

        return value

class LinkResponseModel(BaseModel):
    uid: UUID
    short_url: str
    long_url: HttpUrl
    created_at: datetime
    expires_at: datetime | None = None
