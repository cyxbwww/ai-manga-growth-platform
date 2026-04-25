from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from app.core.database import Base


class MediaAsset(Base):
    __tablename__ = "media_assets"

    id = Column(Integer, primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_type = Column(String(50), nullable=False)
    mime_type = Column(String(120), nullable=False)
    size = Column(Integer, nullable=False)
    object_key = Column(String(500), nullable=False, index=True)
    url = Column(String(1000), nullable=False)
    provider = Column(String(50), nullable=False, default="mock")
    status = Column(String(50), nullable=False, default="pending")
    created_at = Column(DateTime, default=datetime.now)
