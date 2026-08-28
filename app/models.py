from sqlalchemy import Column, Integer, String, Text, DateTime
from datetime import datetime

from .database import Base


class NewsChunk(Base):

    __tablename__ = "news_chunks"

    id = Column(Integer, primary_key=True, index=True)

    title = Column(String(500), nullable=False)

    source = Column(String(200), nullable=False)

    url = Column(String(1000), nullable=False)

    published_at = Column(DateTime, nullable=True)

    chunk_text = Column(Text, nullable=False)

    faiss_id = Column(Integer, unique=True, nullable=False, index=True)

    created_at = Column(
        DateTime,
        default=datetime.utcnow
    )