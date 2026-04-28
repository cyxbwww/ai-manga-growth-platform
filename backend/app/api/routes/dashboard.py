from datetime import datetime, time

from fastapi import APIRouter, Depends
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


router = APIRouter(prefix="/dashboard")


def count_today(db: Session, model) -> int:
    # 今日统计：以本地日期 00:00 为起点统计各模块生成数量。
    today_start = datetime.combine(datetime.now().date(), time.min)
    return db.query(model).filter(model.created_at >= today_start).count()


def count_project_stage(db: Session, stage: str) -> int:
    # 项目阶段分布：只统计未归档项目，便于首页展示当前真实生产状态。
    return db.query(ShortDramaProject).filter(
        ShortDramaProject.stage == stage,
        ShortDramaProject.status != "archived",
    ).count()


def project_to_recent_item(project: ShortDramaProject) -> dict:
    return {
        "id": project.id,
        "name": project.name,
        "genre": project.genre,
        "target_market": project.target_market,
        "stage": project.stage,
        "status": project.status,
        "updated_at": project.updated_at.isoformat(),
    }


def episode_to_recent_item(episode: ShortDramaEpisode, project_name_map: dict[int, str]) -> dict:
    return {
        "id": episode.id,
        "project_id": episode.project_id,
        "project_name": project_name_map.get(episode.project_id, f"项目 {episode.project_id}"),
        "episode_no": episode.episode_no,
        "title": episode.title,
        "stage": episode.stage,
        "storyboard_status": episode.storyboard_status or "pending",
        "localization_status": episode.localization_status or "pending",
        "media_status": episode.media_status or "pending",
        "updated_at": episode.updated_at.isoformat(),
    }


@router.get("/summary")
def get_dashboard_summary(db: Session = Depends(get_db)):
    # 看板汇总接口：从 SQLite 聚合 Project + Episode + Assets 生产链路数据，旧字段继续保留兼容早期页面。
    today_content_plans = count_today(db, ContentPlan)
    today_script_polishes = count_today(db, ScriptPolish)
    today_storyboards = count_today(db, Storyboard)
    today_localizations = count_today(db, Localization)
    today_ad_materials = count_today(db, AdMaterial)
    total_records = (
        db.query(ContentPlan).count()
        + db.query(ScriptPolish).count()
        + db.query(Storyboard).count()
        + db.query(Localization).count()
        + db.query(AdMaterial).count()
    )
    project_total = db.query(ShortDramaProject).filter(ShortDramaProject.status != "archived").count()
    episode_total = db.query(ShortDramaEpisode).filter(ShortDramaEpisode.status != "archived").count()
    storyboard_total = db.query(Storyboard).count()
    localization_total = db.query(Localization).count()
    media_asset_total = db.query(MediaAsset).count()
    ad_material_total = db.query(AdMaterial).count()

    project_stage_distribution = {
        "planning": count_project_stage(db, "planning"),
        "scripting": count_project_stage(db, "scripting"),
        "storyboard": count_project_stage(db, "storyboard"),
        "localization": count_project_stage(db, "localization"),
        "material": count_project_stage(db, "material"),
        "launch": count_project_stage(db, "launch"),
        "completed": count_project_stage(db, "completed"),
    }

    episode_status = {
        "episodeTotal": episode_total,
        "pendingStoryboard": db.query(ShortDramaEpisode).filter(
            ShortDramaEpisode.status != "archived",
            ShortDramaEpisode.storyboard_status != "completed",
        ).count(),
        "completedStoryboard": db.query(ShortDramaEpisode).filter(
            ShortDramaEpisode.status != "archived",
            ShortDramaEpisode.storyboard_status == "completed",
        ).count(),
        "completedLocalization": db.query(ShortDramaEpisode).filter(
            ShortDramaEpisode.status != "archived",
            ShortDramaEpisode.localization_status == "completed",
        ).count(),
        "uploadedMedia": db.query(ShortDramaEpisode).filter(
            ShortDramaEpisode.status != "archived",
            ShortDramaEpisode.media_status == "completed",
        ).count(),
        "completedEpisodes": db.query(ShortDramaEpisode).filter(
            ShortDramaEpisode.status != "archived",
            ShortDramaEpisode.stage == "completed",
        ).count(),
    }

    recent_projects = db.query(ShortDramaProject).filter(
        ShortDramaProject.status != "archived",
    ).order_by(ShortDramaProject.updated_at.desc()).limit(5).all()

    recent_episodes = db.query(ShortDramaEpisode).filter(
        ShortDramaEpisode.status != "archived",
    ).order_by(ShortDramaEpisode.updated_at.desc()).limit(5).all()
    project_ids = {episode.project_id for episode in recent_episodes}
    project_name_map = {
        project.id: project.name
        for project in db.query(ShortDramaProject).filter(ShortDramaProject.id.in_(project_ids)).all()
    } if project_ids else {}

    return {
        "code": 0,
        "message": "success",
        "data": {
            "todayContentPlans": today_content_plans,
            "todayScriptPolishes": today_script_polishes,
            "todayStoryboards": today_storyboards,
            "todayLocalizations": today_localizations,
            "todayAdMaterials": today_ad_materials,
            "totalRecords": total_records,
            "mediaTotal": media_asset_total,
            "mediaVideos": db.query(MediaAsset).filter(MediaAsset.file_type == "video").count(),
            "mediaImages": db.query(MediaAsset).filter(MediaAsset.file_type == "image").count(),
            "mediaUploaded": db.query(MediaAsset).filter(MediaAsset.status == "uploaded").count(),
            "projectTotal": project_total,
            "episodeTotal": episode_total,
            "storyboardTotal": storyboard_total,
            "localizationTotal": localization_total,
            "mediaAssetTotal": media_asset_total,
            "adMaterialTotal": ad_material_total,
            "projectStageDistribution": project_stage_distribution,
            "episodeStatus": episode_status,
            "recentProjects": [project_to_recent_item(project) for project in recent_projects],
            "recentEpisodes": [episode_to_recent_item(episode, project_name_map) for episode in recent_episodes],
        },
    }
