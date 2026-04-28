from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.core.database import Base


class ContentPlan(Base):
    # 内容策划生成记录：保存输入参数和结构化生成结果。
    __tablename__ = "content_plans"

    id = Column(Integer, primary_key=True, index=True)
    # project_id 用于把 AI 生成结果绑定到短剧项目，当前先做弱关联，后续可升级为外键约束。
    project_id = Column(Integer, nullable=True, index=True)
    project_name = Column(String(255), nullable=False)
    genre = Column(String(100), nullable=False)
    market = Column(String(100), nullable=False)
    language = Column(String(100), nullable=False)
    duration = Column(String(50), nullable=False)
    selling_point = Column(Text, nullable=False)
    result_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
