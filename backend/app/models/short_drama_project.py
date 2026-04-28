from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.core.database import Base


class ShortDramaProject(Base):
    # 短剧项目主表：后续内容策划、剧本、分镜、素材等模块都会逐步通过 projectId 绑定到这里。
    __tablename__ = "short_drama_projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    genre = Column(String(100), nullable=False, index=True)
    target_market = Column(String(100), nullable=False, index=True)
    language = Column(String(50), nullable=False)
    episode_count = Column(Integer, default=60, nullable=False)
    stage = Column(String(50), default="planning", nullable=False, index=True)
    description = Column(Text, nullable=True)
    owner = Column(String(100), nullable=True)
    priority = Column(String(20), default="medium", nullable=False)
    status = Column(String(20), default="active", nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
