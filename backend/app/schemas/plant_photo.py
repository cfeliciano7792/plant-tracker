from datetime import datetime

from pydantic import BaseModel


class PhotoOut(BaseModel):
    id: int
    content_type: str
    file_size: int
    uploaded_at: datetime

    model_config = {"from_attributes": True}
