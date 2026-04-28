from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.core.database import Base


class ScriptPolish(Base):
    # 剧本打磨记录：directions_json 保存多选方向，result_json 保存打磨结果。
    __tablename__ = "script_polishes"

    id = Column(Integer, primary_key=True, index=True)
    # project_id 用于把 AI 生成结果绑定到短剧项目，当前先做弱关联，后续可升级为外键约束。
    project_id = Column(Integer, nullable=True, index=True)
    content_plan_id = Column(Integer, nullable=True)
    # language 保存字典 value，例如 en-US；展示名称由前端字典转换。
    language = Column(String(50), nullable=True)
    title = Column(String(255), nullable=False)
    original_script = Column(Text, nullable=False)
    directions_json = Column(Text, nullable=False)
    result_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
