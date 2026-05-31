from datetime import datetime

from pydantic import BaseModel, Field


class Memory(BaseModel):
    id: str
    person_id: str | None
    content: str
    importance: int = Field(ge=1, le=5)
    created_at: datetime
