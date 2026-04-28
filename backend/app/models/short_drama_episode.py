from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text, UniqueConstraint

from app.core.database import Base


class ShortDramaEpisode(Base):
    # 短剧分集表：Episode 是短剧生产的单集推进单元，后续剧本、分镜、本地化、媒体资产可继续绑定到这里。
    __tablename__ = "short_drama_episodes"
    __table_args__ = (
        UniqueConstraint("project_id", "episode_no", name="uq_short_drama_episode_project_no"),
    )

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, nullable=False, index=True)
    episode_no = Column(Integer, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    summary = Column(Text, nullable=True)
    stage = Column(String(50), default="planning", nullable=False, index=True)
    status = Column(String(20), default="active", nullable=False, index=True)
    script_status = Column(String(50), default="pending", nullable=True)
    storyboard_status = Column(String(50), default="pending", nullable=True)
    localization_status = Column(String(50), default="pending", nullable=True)
    media_status = Column(String(50), default="pending", nullable=True)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now, nullable=False)
