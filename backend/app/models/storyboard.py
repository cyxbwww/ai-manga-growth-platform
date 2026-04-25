from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.core.database import Base


class Storyboard(Base):
    # AI 分镜记录：保存剧本、风格、分镜数量和完整分镜 JSON。
    __tablename__ = "storyboards"

    id = Column(Integer, primary_key=True, index=True)
    content_plan_id = Column(Integer, nullable=True)
    script_polish_id = Column(Integer, nullable=True)
    title = Column(String(255), nullable=False)
    script = Column(Text, nullable=False)
    style = Column(String(100), nullable=False)
    scene_count = Column(Integer, nullable=False)
    result_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
