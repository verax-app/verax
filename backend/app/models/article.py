from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text
from sqlalchemy.sql import func
from app.database import Base


class Article(Base):
    __tablename__ = "articles"

    id               = Column(Integer, primary_key=True, index=True)
    title            = Column(String(500), nullable=False)
    url              = Column(String(1000), unique=True, index=True, nullable=False)
    text             = Column(Text, nullable=True)
    summary          = Column(Text, nullable=True)
    source_name      = Column(String(100))
    category         = Column(String(50), index=True, default="general")
    region           = Column(String(50), index=True, default="global")
    language         = Column(String(10), index=True, default="en")
    bias             = Column(String(20), nullable=True)
    bias_confidence  = Column(Integer, nullable=True)
    bias_reason      = Column(Text, nullable=True)
    tags             = Column(String(500), nullable=True)
    read_time        = Column(Integer, default=60)
    summarized       = Column(Boolean, default=False, index=True)
    published_at     = Column(DateTime, nullable=True, index=True)
    created_at       = Column(DateTime, server_default=func.now())
