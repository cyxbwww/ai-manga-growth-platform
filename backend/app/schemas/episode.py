from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict


class ShortDramaEpisodeCreate(BaseModel):
    # 新增分集时，project_id 会以路径参数为准；保留字段是为了前端类型和后续扩展更直观。
    project_id: int
    episode_no: int
    title: str
    summary: Optional[str] = None
    stage: str = "planning"
    status: str = "active"


class ShortDramaEpisodeUpdate(BaseModel):
    # 分集编辑采用局部更新，方便只调整某个生产状态或标题摘要。
    episode_no: Optional[int] = None
    title: Optional[str] = None
    summary: Optional[str] = None
    stage: Optional[str] = None
    status: Optional[str] = None
    script_status: Optional[str] = None
    storyboard_status: Optional[str] = None
    localization_status: Optional[str] = None
    media_status: Optional[str] = None


class ShortDramaEpisodeOut(BaseModel):
    id: int
    project_id: int
    episode_no: int
    title: str
    summary: Optional[str] = None
    stage: str
    status: str
    script_status: Optional[str] = None
    storyboard_status: Optional[str] = None
    localization_status: Optional[str] = None
    media_status: Optional[str] = None
    # 分集级资产聚合字段：仅由列表接口运行时统计，不写入 short_drama_episodes 表。
    storyboard_count: int = 0
    localization_count: int = 0
    media_asset_count: int = 0
    ad_material_count: int = 0
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ShortDramaEpisodeListResponse(BaseModel):
    # 列表返回 items + total，后续可直接接分页器。
    items: list[ShortDramaEpisodeOut]
    total: int
