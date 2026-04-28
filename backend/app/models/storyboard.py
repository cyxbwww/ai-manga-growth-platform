from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.core.database import Base


class Storyboard(Base):
    # AI 分镜记录：保存剧本、风格、分镜数量和完整分镜 JSON。
    __tablename__ = "storyboards"

    id = Column(Integer, primary_key=True, index=True)
    # project_id 用于把 AI 生成结果绑定到短剧项目，当前先做弱关联，后续可升级为外键约束。
    project_id = Column(Integer, nullable=True, index=True)
    # episode_id / episode_no 用于把分镜绑定到具体短剧分集，当前采用弱关联以兼容旧演示数据。
    episode_id = Column(Integer, nullable=True, index=True)
    episode_no = Column(Integer, nullable=True, index=True)
    content_plan_id = Column(Integer, nullable=True)
    script_polish_id = Column(Integer, nullable=True)
    title = Column(String(255), nullable=False)
    script = Column(Text, nullable=False)
    style = Column(String(100), nullable=False)
    scene_count = Column(Integer, nullable=False)
    result_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
