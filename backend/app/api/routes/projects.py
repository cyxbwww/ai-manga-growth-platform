from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.ad_material import AdMaterial
from app.models.content_plan import ContentPlan
from app.models.localization import Localization
from app.models.media_asset import MediaAsset
from app.models.script_polish import ScriptPolish
from app.models.short_drama_episode import ShortDramaEpisode
from app.models.short_drama_project import ShortDramaProject
from app.models.storyboard import Storyboard
from app.schemas.project import ShortDramaProjectCreate, ShortDramaProjectUpdate


router = APIRouter(prefix="/projects")


def schema_to_dict(schema, exclude_unset: bool = False) -> dict:
    # 兼容 Pydantic v1 / v2：当前项目只需要取出用户提交字段，不强绑定具体版本。
    if hasattr(schema, "model_dump"):
        return schema.model_dump(exclude_unset=exclude_unset)
    return schema.dict(exclude_unset=exclude_unset)


def project_to_dict(project: ShortDramaProject) -> dict:
    # 统一把 ORM 对象转为接口结构，字段名与数据库模型保持一致，方便面试时讲清数据主线。
    return {
        "id": project.id,
        "name": project.name,
        "genre": project.genre,
        "target_market": project.target_market,
        "language": project.language,
        "episode_count": project.episode_count,
        "stage": project.stage,
        "description": project.description,
        "owner": project.owner,
        "priority": project.priority,
        "status": project.status,
        "created_at": project.created_at.isoformat(),
        "updated_at": project.updated_at.isoformat(),
    }


def get_project_or_404(project_id: int, db: Session) -> ShortDramaProject:
    project = db.query(ShortDramaProject).filter(ShortDramaProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    return project


PIPELINE_DEFINITIONS = [
    {"key": "planning", "title": "内容策划", "stat": "content_plan_count", "description": "完成题材、目标市场、核心卖点和前三秒钩子设计。"},
    {"key": "scripting", "title": "剧本打磨", "stat": "script_count", "description": "优化节奏、冲突、反转和情绪张力。"},
    {"key": "storyboard", "title": "AI分镜", "stat": "storyboard_count", "description": "拆解可生产的镜头、画面提示词和运镜提示词。"},
    {"key": "localization", "title": "多语种本地化", "stat": "localization_count", "description": "生成目标市场更自然的字幕、配音和本地化表达。"},
    {"key": "material", "title": "广告素材", "stat": "ad_material_count", "description": "生成短视频投放标题、钩子、文案和封面提示词。"},
    {"key": "media", "title": "媒体资产", "stat": "media_asset_count", "description": "管理视频、图片、字幕等生产素材。"},
    {"key": "launch", "title": "投放分析", "stat": "ad_material_count", "description": "通过 CTR、CVR、ROI 反向优化内容生产。"},
]

STAGE_ORDER = ["planning", "scripting", "storyboard", "localization", "material", "media", "launch", "completed"]

MOCK_STATS_BY_STAGE = {
    "planning": {"content_plan_count": 1, "script_count": 0, "storyboard_count": 0, "localization_count": 0, "ad_material_count": 0, "media_asset_count": 0},
    "scripting": {"content_plan_count": 1, "script_count": 1, "storyboard_count": 0, "localization_count": 0, "ad_material_count": 0, "media_asset_count": 0},
    "storyboard": {"content_plan_count": 1, "script_count": 2, "storyboard_count": 3, "localization_count": 0, "ad_material_count": 0, "media_asset_count": 1},
    "localization": {"content_plan_count": 1, "script_count": 2, "storyboard_count": 3, "localization_count": 2, "ad_material_count": 0, "media_asset_count": 1},
    "material": {"content_plan_count": 1, "script_count": 2, "storyboard_count": 3, "localization_count": 2, "ad_material_count": 4, "media_asset_count": 3},
    "launch": {"content_plan_count": 1, "script_count": 2, "storyboard_count": 3, "localization_count": 2, "ad_material_count": 6, "media_asset_count": 5},
    "completed": {"content_plan_count": 1, "script_count": 2, "storyboard_count": 3, "localization_count": 2, "ad_material_count": 6, "media_asset_count": 5},
}


def count_by_project_if_possible(db: Session, model, project_id: int) -> Optional[int]:
    # 当前 overview 先兼容旧数据结构，后续第 3 步会逐步把生成结果绑定到 projectId。
    if hasattr(model, "project_id"):
        try:
            return db.query(model).filter(model.project_id == project_id).count()
        except Exception as exc:
            # 旧 SQLite 表可能暂时缺少 project_id 列，统计失败时回退到 mock，避免详情页不可用。
            db.rollback()
            print(f"项目 overview 真实统计失败，使用兼容统计：model={model.__tablename__}, error={exc}")
            return None
    return None


def build_project_stats(project: ShortDramaProject, db: Session) -> dict:
    # 如果旧表还没有 project_id，则使用与项目阶段匹配的 mock 统计，保证详情页面试演示不空白。
    mock_stats = MOCK_STATS_BY_STAGE.get(project.stage, MOCK_STATS_BY_STAGE["planning"]).copy()
    try:
        # Episode 是第 5 步新增的分集维度，优先统计当前项目下未归档分集；失败时兜底项目计划集数。
        mock_stats["episode_count"] = db.query(ShortDramaEpisode).filter(
            ShortDramaEpisode.project_id == project.id,
            ShortDramaEpisode.status != "archived",
        ).count()
    except Exception as exc:
        db.rollback()
        print(f"项目 overview 分集统计失败，使用项目计划集数兜底：project_id={project.id}, error={exc}")
        mock_stats["episode_count"] = project.episode_count or 0
    model_map = {
        "content_plan_count": ContentPlan,
        "script_count": ScriptPolish,
        "storyboard_count": Storyboard,
        "localization_count": Localization,
        "ad_material_count": AdMaterial,
        "media_asset_count": MediaAsset,
    }
    for key, model in model_map.items():
        real_count = count_by_project_if_possible(db, model, project.id)
        if real_count is not None:
            mock_stats[key] = real_count
    return mock_stats


def build_pipeline(stage: str, stats: dict) -> list[dict]:
    if stage == "completed":
        current_index = len(STAGE_ORDER) - 1
    else:
        current_index = STAGE_ORDER.index(stage) if stage in STAGE_ORDER else 0

    items = []
    for item in PIPELINE_DEFINITIONS:
        item_index = STAGE_ORDER.index(item["key"])
        if stage == "completed" or item_index < current_index:
            status = "completed"
        elif item_index == current_index:
            status = "processing"
        else:
            status = "pending"
        items.append(
            {
                "key": item["key"],
                "title": item["title"],
                "status": status,
                "count": stats.get(item["stat"], 0),
                "description": item["description"],
            }
        )
    return items


def recent_from_model(db: Session, model, title_field: str, item_type: str, status: str, project_id: int) -> list[dict]:
    # 当前先尽量按 project_id 取数据；如果旧表没有 project_id，则返回空数组，由前端展示空状态。
    if not hasattr(model, "project_id"):
        return []
    rows = db.query(model).filter(model.project_id == project_id).order_by(model.created_at.desc()).limit(3).all()
    return [
        {
            "id": row.id,
            "title": getattr(row, title_field, f"{item_type}{row.id}"),
            "type": item_type,
            "status": status,
            "created_at": row.created_at.isoformat(),
            "episode_id": getattr(row, "episode_id", None),
            "episode_no": getattr(row, "episode_no", None),
        }
        for row in rows
    ]


@router.get("")
def list_projects(
    keyword: Optional[str] = Query(default=None),
    genre: Optional[str] = Query(default=None),
    stage: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    # 项目列表支持关键词和基础维度筛选，默认不强制过滤 active，方便查看归档项目。
    query = db.query(ShortDramaProject)
    if keyword:
        like_keyword = f"%{keyword}%"
        query = query.filter(or_(ShortDramaProject.name.like(like_keyword), ShortDramaProject.description.like(like_keyword)))
    if genre:
        query = query.filter(ShortDramaProject.genre == genre)
    if stage:
        query = query.filter(ShortDramaProject.stage == stage)
    if status:
        query = query.filter(ShortDramaProject.status == status)

    total = query.count()
    items = query.order_by(ShortDramaProject.updated_at.desc()).offset(skip).limit(limit).all()
    return {"code": 0, "message": "success", "data": {"items": [project_to_dict(item) for item in items], "total": total}}


@router.post("")
def create_project(payload: ShortDramaProjectCreate, db: Session = Depends(get_db)):
    # 新建项目是后续全链路生产的入口，默认进入策划中和进行中状态。
    data = schema_to_dict(payload)
    project = ShortDramaProject(
        name=data["name"],
        genre=data["genre"],
        target_market=data["target_market"],
        language=data["language"],
        episode_count=data.get("episode_count") or 60,
        stage=data.get("stage") or "planning",
        description=data.get("description"),
        owner=data.get("owner"),
        priority=data.get("priority") or "medium",
        status=data.get("status") or "active",
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return {"code": 0, "message": "success", "data": project_to_dict(project)}


@router.get("/{project_id}/overview")
def get_project_overview(project_id: int, db: Session = Depends(get_db)):
    # 项目详情页聚合接口：把基础信息、统计、生产链路和最近数据一次性返回给前端。
    project = get_project_or_404(project_id, db)
    stats = build_project_stats(project, db)
    overview = {
        "project": project_to_dict(project),
        "stats": stats,
        "pipeline": build_pipeline(project.stage, stats),
        "recent_storyboards": recent_from_model(db, Storyboard, "title", "AI分镜", "待生成", project.id),
        "recent_ad_materials": recent_from_model(db, AdMaterial, "project_name", "广告素材", "已生成", project.id),
        "recent_media_assets": recent_from_model(db, MediaAsset, "original_filename", "媒体资产", "已上传", project.id),
    }
    return {"code": 0, "message": "success", "data": overview}


@router.get("/{project_id}")
def get_project_detail(project_id: int, db: Session = Depends(get_db)):
    project = get_project_or_404(project_id, db)
    return {"code": 0, "message": "success", "data": project_to_dict(project)}


@router.patch("/{project_id}")
def update_project(project_id: int, payload: ShortDramaProjectUpdate, db: Session = Depends(get_db)):
    project = get_project_or_404(project_id, db)
    data = schema_to_dict(payload, exclude_unset=True)
    field_map = {
        "target_market": "target_market",
        "episode_count": "episode_count",
    }
    for key, value in data.items():
        model_field = field_map.get(key, key)
        setattr(project, model_field, value)
    project.updated_at = datetime.now()
    db.commit()
    db.refresh(project)
    return {"code": 0, "message": "success", "data": project_to_dict(project)}


@router.delete("/{project_id}")
def archive_project(project_id: int, db: Session = Depends(get_db)):
    # 归档采用软删除，不物理删除项目，避免影响后续链路数据绑定。
    project = get_project_or_404(project_id, db)
    project.status = "archived"
    project.updated_at = datetime.now()
    db.commit()
    db.refresh(project)
    return {"code": 0, "message": "success", "data": project_to_dict(project)}
