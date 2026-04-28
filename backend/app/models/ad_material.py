from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.core.database import Base


class AdMaterial(Base):
    # 海外投放素材记录：保存素材生成输入和素材包结果。
    __tablename__ = "ad_materials"

    id = Column(Integer, primary_key=True, index=True)
    # project_id 用于把广告素材绑定到短剧项目，当前先做弱关联，兼容旧演示数据。
    project_id = Column(Integer, nullable=True, index=True)
    # episode_id / episode_no 用于把广告素材可选绑定到具体短剧分集；为空时代表项目级广告素材。
    episode_id = Column(Integer, nullable=True, index=True)
    episode_no = Column(Integer, nullable=True, index=True)
    content_plan_id = Column(Integer, nullable=True)
    script_polish_id = Column(Integer, nullable=True)
    storyboard_id = Column(Integer, nullable=True)
    localization_id = Column(Integer, nullable=True)
    project_name = Column(String(255), nullable=False)
    market = Column(String(100), nullable=False)
    platform = Column(String(100), nullable=False)
    content_type = Column(String(100), nullable=False)
    result_json = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.now, nullable=False)
