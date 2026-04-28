from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ShortDramaProjectBase(BaseModel):
    # 项目基础字段：与数据库模型保持一致，前后端都围绕这些字段做项目管理。
    name: str
    genre: str
    target_market: str
    language: str
    episode_count: int = 60
    stage: str = "planning"
    description: Optional[str] = None
    owner: Optional[str] = None
    priority: str = "medium"
    status: str = "active"


class ShortDramaProjectCreate(ShortDramaProjectBase):
    # 新建项目时允许前端不传阶段、状态和优先级，由后端默认填充。
    pass


class ShortDramaProjectUpdate(BaseModel):
    # 修改项目时所有字段可选，只更新用户传入的字段。
    name: Optional[str] = None
    genre: Optional[str] = None
    target_market: Optional[str] = None
    language: Optional[str] = None
    episode_count: Optional[int] = None
    stage: Optional[str] = None
    description: Optional[str] = None
    owner: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None


class ShortDramaProjectOut(ShortDramaProjectBase):
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ShortDramaProjectListResponse(BaseModel):
    # 列表接口返回 items + total，方便后续接分页器。
    items: list[ShortDramaProjectOut]
    total: int


class ProjectStats(BaseModel):
    # 项目总览统计：当前先兼容旧数据结构，后续会逐步改为真实 projectId 统计。
    content_plan_count: int
    episode_count: int
    script_count: int
    storyboard_count: int
    localization_count: int
    ad_material_count: int
    media_asset_count: int


class ProjectPipelineItem(BaseModel):
    key: str
    title: str
    status: str
    count: int
    description: str


class ProjectRecentItem(BaseModel):
    id: int
    title: str
    type: str
    status: str
    created_at: str


class ProjectOverview(BaseModel):
    project: ShortDramaProjectOut
    stats: ProjectStats
    pipeline: list[ProjectPipelineItem]
    recent_storyboards: list[ProjectRecentItem]
    recent_ad_materials: list[ProjectRecentItem]
    recent_media_assets: list[ProjectRecentItem]
