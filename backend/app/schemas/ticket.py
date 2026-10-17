from datetime import datetime

from pydantic import BaseModel, ConfigDict


class TicketResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    reason: str
    conversation: str
    status: str
    created_at: datetime


class TicketStatusUpdate(BaseModel):
    status: str