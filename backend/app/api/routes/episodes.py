from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.ad_material import AdMaterial
from app.models.content_plan import ContentPlan
from app.models.localization import Localization
from app.models.media_asset import MediaAsset
from app.models.short_drama_episode import ShortDramaEpisode
from app.models.short_drama_project import ShortDramaProject
from app.models.storyboard import Storyboard
from app.schemas.episode import EpisodeOutlineGenerateRequest, ShortDramaEpisodeCreate, ShortDramaEpisodeUpdate
from app.services.episode_outline_service import generate_episode_outline_items


router = APIRouter()


def schema_to_dict(schema, exclude_unset: bool = False) -> dict:
    # 兼容 Pydantic v1 / v2，避免项目依赖版本变化影响接口更新逻辑。
    if hasattr(schema, "model_dump"):
        return schema.model_dump(exclude_unset=exclude_unset)
    return schema.dict(exclude_unset=exclude_unset)


def episode_to_dict(episode: ShortDramaEpisode) -> dict:
    # 统一输出分集结构，前端列表页直接使用 snake_case 字段。
    return {
        "id": episode.id,
        "project_id": episode.project_id,
        "episode_no": episode.episode_no,
        "title": episode.title,
        "summary": episode.summary,
        "stage": episode.stage,
        "status": episode.status,
        "script_status": episode.script_status,
        "storyboard_status": episode.storyboard_status,
        "localization_status": episode.localization_status,
        "media_status": episode.media_status,
        "created_at": episode.created_at.isoformat(),
        "updated_at": episode.updated_at.isoformat(),
    }


def count_episode_asset(db: Session, model, project_id: int, episode_id: int) -> int:
    # 分集级资产聚合：按 project_id + episode_id 统计每一集沉淀的生产资产，统计失败时兜底为 0，避免影响分集列表主流程。
    try:
        return db.query(model).filter(model.project_id == project_id, model.episode_id == episode_id).count()
    except Exception as exc:
        db.rollback()
        print(f"统计分集资产失败：{model.__tablename__} project_id={project_id} episode_id={episode_id}, error={exc}")
        return 0


def episode_asset_counts(episode: ShortDramaEpisode, db: Session) -> dict:
    # 这里只做接口聚合展示，不写入数据库，方便面试时说明“项目 -> 分集 -> 生产资产”的沉淀链路。
    return {
        "storyboard_count": count_episode_asset(db, Storyboard, episode.project_id, episode.id),
        "localization_count": count_episode_asset(db, Localization, episode.project_id, episode.id),
        "media_asset_count": count_episode_asset(db, MediaAsset, episode.project_id, episode.id),
        "ad_material_count": count_episode_asset(db, AdMaterial, episode.project_id, episode.id),
    }


def episode_to_dict_with_counts(episode: ShortDramaEpisode, db: Session) -> dict:
    data = episode_to_dict(episode)
    data.update(episode_asset_counts(episode, db))
    return data


def get_project_or_404(project_id: int, db: Session) -> ShortDramaProject:
    project = db.query(ShortDramaProject).filter(ShortDramaProject.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="短剧项目不存在")
    return project


def get_episode_or_404(episode_id: int, db: Session) -> ShortDramaEpisode:
    episode = db.query(ShortDramaEpisode).filter(ShortDramaEpisode.id == episode_id).first()
    if not episode:
        raise HTTPException(status_code=404, detail="分集不存在")
    return episode


def ensure_episode_no_unique(db: Session, project_id: int, episode_no: int, exclude_id: Optional[int] = None) -> None:
    query = db.query(ShortDramaEpisode).filter(
        ShortDramaEpisode.project_id == project_id,
        ShortDramaEpisode.episode_no == episode_no,
    )
    if exclude_id is not None:
        query = query.filter(ShortDramaEpisode.id != exclude_id)
    if query.first():
        raise HTTPException(status_code=400, detail="同一短剧项目下集数不能重复")


@router.get("/projects/{project_id}/episodes")
def list_project_episodes(
    project_id: int,
    keyword: Optional[str] = Query(default=None),
    stage: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=200),
    db: Session = Depends(get_db),
):
    get_project_or_404(project_id, db)
    query = db.query(ShortDramaEpisode).filter(ShortDramaEpisode.project_id == project_id)
    if keyword:
        like_keyword = f"%{keyword}%"
        query = query.filter(or_(ShortDramaEpisode.title.like(like_keyword), ShortDramaEpisode.summary.like(like_keyword)))
    if stage:
        query = query.filter(ShortDramaEpisode.stage == stage)
    if status:
        query = query.filter(ShortDramaEpisode.status == status)

    total = query.count()
    items = query.order_by(ShortDramaEpisode.episode_no.asc()).offset(skip).limit(limit).all()
    return {"code": 0, "message": "success", "data": {"items": [episode_to_dict_with_counts(item, db) for item in items], "total": total}}


@router.post("/projects/{project_id}/episodes")
def create_project_episode(project_id: int, payload: ShortDramaEpisodeCreate, db: Session = Depends(get_db)):
    get_project_or_404(project_id, db)
    data = schema_to_dict(payload)
    ensure_episode_no_unique(db, project_id, data["episode_no"])
    episode = ShortDramaEpisode(
        # 路径参数是最终归属来源，避免前端 body 误传 project_id 造成跨项目写入。
        project_id=project_id,
        episode_no=data["episode_no"],
        title=data["title"],
        summary=data.get("summary"),
        stage=data.get("stage") or "planning",
        status=data.get("status") or "active",
    )
    db.add(episode)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="同一短剧项目下集数不能重复")
    db.refresh(episode)
    return {"code": 0, "message": "success", "data": episode_to_dict(episode)}


@router.post("/projects/{project_id}/episodes/batch-generate")
def batch_generate_project_episodes(project_id: int, db: Session = Depends(get_db)):
    project = get_project_or_404(project_id, db)
    existing = db.query(ShortDramaEpisode).filter(ShortDramaEpisode.project_id == project_id).order_by(ShortDramaEpisode.episode_no.asc()).all()
    if existing:
        return {
            "code": 0,
            "message": "当前项目已存在分集，未重复生成",
            "data": {"items": [episode_to_dict(item) for item in existing], "total": len(existing)},
        }

    count = project.episode_count or 12
    episodes = [
        ShortDramaEpisode(
            project_id=project_id,
            episode_no=index,
            title=f"第 {index} 集",
            summary="待补充剧情摘要",
            stage="planning",
            status="active",
        )
        for index in range(1, count + 1)
    ]
    db.add_all(episodes)
    db.commit()
    for episode in episodes:
        db.refresh(episode)
    return {"code": 0, "message": "success", "data": {"items": [episode_to_dict(item) for item in episodes], "total": len(episodes)}}


@router.post("/projects/{project_id}/episodes/generate-outline")
def generate_project_episode_outline(project_id: int, payload: EpisodeOutlineGenerateRequest, db: Session = Depends(get_db)):
    # 分集大纲由项目级内容策划拆解而来，写入 Episode 表后可在分集管理页逐集调整。
    project = get_project_or_404(project_id, db)
    if payload.episode_count < 1 or payload.episode_count > 30:
        raise HTTPException(status_code=400, detail="生成集数需在 1～30 之间")
    if payload.start_episode_no < 1:
        raise HTTPException(status_code=400, detail="起始集数不能小于 1")

    content_plan = None
    if payload.content_plan_id:
        content_plan = db.query(ContentPlan).filter(ContentPlan.id == payload.content_plan_id).first()
        if not content_plan or content_plan.project_id != project_id:
            raise HTTPException(status_code=404, detail="内容策划记录不存在或不属于当前项目")
    else:
        content_plan = db.query(ContentPlan).filter(
            ContentPlan.project_id == project_id,
        ).order_by(ContentPlan.created_at.desc()).first()

    outline_items, generation_source = generate_episode_outline_items(project, content_plan, payload.episode_count, payload.start_episode_no)
    created_count = 0
    updated_count = 0
    skipped_count = 0
    episodes: list[ShortDramaEpisode] = []

    for item in outline_items:
        episode = db.query(ShortDramaEpisode).filter(
            ShortDramaEpisode.project_id == project_id,
            ShortDramaEpisode.episode_no == item["episode_no"],
        ).first()
        if episode and not payload.overwrite:
            skipped_count += 1
            episodes.append(episode)
            continue

        if episode:
            episode.title = item["title"]
            episode.summary = item["summary"]
            episode.stage = "scripting"
            episode.status = "active"
            episode.updated_at = datetime.now()
            updated_count += 1
        else:
            episode = ShortDramaEpisode(
                project_id=project_id,
                episode_no=item["episode_no"],
                title=item["title"],
                summary=item["summary"],
                stage="scripting",
                status="active",
                script_status="pending",
                storyboard_status="pending",
                localization_status="pending",
                media_status="pending",
            )
            db.add(episode)
            created_count += 1
        episodes.append(episode)

    db.commit()
    for episode in episodes:
        db.refresh(episode)

    return {
        "code": 0,
        "message": "success",
        "data": {
            "project_id": project_id,
            "content_plan_id": content_plan.id if content_plan else None,
            "generation_source": generation_source,
            "created_count": created_count,
            "updated_count": updated_count,
            "skipped_count": skipped_count,
            "items": [episode_to_dict(item) for item in episodes],
        },
    }


@router.get("/episodes/{episode_id}")
def get_episode_detail(episode_id: int, db: Session = Depends(get_db)):
    episode = get_episode_or_404(episode_id, db)
    return {"code": 0, "message": "success", "data": episode_to_dict(episode)}


@router.patch("/episodes/{episode_id}")
def update_episode(episode_id: int, payload: ShortDramaEpisodeUpdate, db: Session = Depends(get_db)):
    episode = get_episode_or_404(episode_id, db)
    data = schema_to_dict(payload, exclude_unset=True)
    if "episode_no" in data and data["episode_no"] != episode.episode_no:
        ensure_episode_no_unique(db, episode.project_id, data["episode_no"], exclude_id=episode.id)
    for key, value in data.items():
        setattr(episode, key, value)
    episode.updated_at = datetime.now()
    db.commit()
    db.refresh(episode)
    return {"code": 0, "message": "success", "data": episode_to_dict(episode)}


@router.delete("/episodes/{episode_id}")
def archive_episode(episode_id: int, db: Session = Depends(get_db)):
    # 分集采用软删除，保留历史生产数据，避免后续生成资产断链。
    episode = get_episode_or_404(episode_id, db)
    episode.status = "archived"
    episode.updated_at = datetime.now()
    db.commit()
    db.refresh(episode)
    return {"code": 0, "message": "success", "data": episode_to_dict(episode)}
