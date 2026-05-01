from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ArticleOut(BaseModel):
    id:              int
    title:           str
    url:             str
    summary:         Optional[str]
    source_name:     str
    category:        str
    region:          str
    language:        str
    bias:            Optional[str]
    bias_confidence: Optional[int]
    bias_reason:     Optional[str]
    tags:            Optional[str]
    read_time:       int
    published_at:    Optional[datetime]
    created_at:      datetime

    model_config = {"from_attributes": True}
