from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String

from app.core.database import Base


class MediaAsset(Base):
    __tablename__ = "media_assets"

    id = Column(Integer, primary_key=True, index=True)
    # project_id 用于把上传素材绑定到短剧项目，当前先做弱关联，避免旧库迁移成本过高。
    project_id = Column(Integer, nullable=True, index=True)
    # episode_id / episode_no 用于把视频、图片、字幕等媒体资产绑定到具体短剧分集，当前采用弱关联以兼容旧数据。
    episode_id = Column(Integer, nullable=True, index=True)
    episode_no = Column(Integer, nullable=True, index=True)
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
