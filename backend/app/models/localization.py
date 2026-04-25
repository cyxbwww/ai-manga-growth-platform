from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.core.database import Base


class Localization(Base):
    # 本地化记录：保存市场、语言、策略和字幕处理结果。
    __tablename__ = "localizations"

    id = Column(Integer, primary_key=True, index=True)
    content_plan_id = Column(Integer, nullable=True)
    script_polish_id = Column(Integer, nullable=True)
    storyboard_id = Column(Integer, nullable=True)
    market = Column(String(100), nullable=False)
    language = Column(String(100), nullable=False)
    strategy = Column(String(100), nullable=False)
    result_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
