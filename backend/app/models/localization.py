from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.core.database import Base


class Localization(Base):
    # 本地化记录：保存市场、语言、策略和字幕处理结果。
    __tablename__ = "localizations"

    id = Column(Integer, primary_key=True, index=True)
    # project_id 用于把本地化结果绑定到短剧项目，当前先做弱关联，后续可升级为外键约束。
    project_id = Column(Integer, nullable=True, index=True)
    # episode_id / episode_no 用于把本地化版本绑定到具体短剧分集，当前采用弱关联以兼容旧数据。
    episode_id = Column(Integer, nullable=True, index=True)
    episode_no = Column(Integer, nullable=True, index=True)
    content_plan_id = Column(Integer, nullable=True)
    script_polish_id = Column(Integer, nullable=True)
    storyboard_id = Column(Integer, nullable=True)
    market = Column(String(100), nullable=False)
    language = Column(String(100), nullable=False)
    strategy = Column(String(100), nullable=False)
    result_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
