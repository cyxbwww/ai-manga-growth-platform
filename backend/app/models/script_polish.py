from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.core.database import Base


class ScriptPolish(Base):
    # 剧本打磨记录：directions_json 保存多选方向，result_json 保存打磨结果。
    __tablename__ = "script_polishes"

    id = Column(Integer, primary_key=True, index=True)
    content_plan_id = Column(Integer, nullable=True)
    title = Column(String(255), nullable=False)
    original_script = Column(Text, nullable=False)
    directions_json = Column(Text, nullable=False)
    result_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
