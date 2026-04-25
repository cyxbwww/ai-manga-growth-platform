import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.ad_material import AdMaterial
from app.models.content_plan import ContentPlan
from app.models.localization import Localization
from app.models.script_polish import ScriptPolish
from app.models.storyboard import Storyboard


router = APIRouter(prefix="/pipeline")


def parse_result(value: str) -> dict:
    # 旧数据可能不是合法 JSON，接口兜底为空对象，避免链路详情报错。
    try:
        return json.loads(value)
    except Exception:
        return {}


def content_plan_item(item: ContentPlan | None):
    if not item:
        return None
    return {
        "id": item.id,
        "projectName": item.project_name,
        "genre": item.genre,
        "market": item.market,
        "language": item.language,
        "duration": item.duration,
        "sellingPoint": item.selling_point,
        "result": parse_result(item.result_json),
        "createdAt": item.created_at.isoformat(),
    }


def script_item(item: ScriptPolish):
    return {
        "id": item.id,
        "contentPlanId": item.content_plan_id,
        "title": item.title,
        "script": item.original_script,
        "directions": parse_result(item.directions_json) if item.directions_json.startswith("[") else [],
        "result": parse_result(item.result_json),
        "createdAt": item.created_at.isoformat(),
    }


def storyboard_item(item: Storyboard):
    return {
        "id": item.id,
        "contentPlanId": item.content_plan_id,
        "scriptPolishId": item.script_polish_id,
        "title": item.title,
        "script": item.script,
        "style": item.style,
        "sceneCount": item.scene_count,
        "result": parse_result(item.result_json),
        "createdAt": item.created_at.isoformat(),
    }


def localization_item(item: Localization):
    return {
        "id": item.id,
        "contentPlanId": item.content_plan_id,
        "scriptPolishId": item.script_polish_id,
        "storyboardId": item.storyboard_id,
        "market": item.market,
        "language": item.language,
        "strategy": item.strategy,
        "result": parse_result(item.result_json),
        "createdAt": item.created_at.isoformat(),
    }


def ad_item(item: AdMaterial):
    return {
        "id": item.id,
        "contentPlanId": item.content_plan_id,
        "scriptPolishId": item.script_polish_id,
        "storyboardId": item.storyboard_id,
        "localizationId": item.localization_id,
        "projectName": item.project_name,
        "market": item.market,
        "platform": item.platform,
        "contentType": item.content_type,
        "result": parse_result(item.result_json),
        "createdAt": item.created_at.isoformat(),
    }


@router.get("/{content_plan_id}")
def get_pipeline_detail(content_plan_id: int, db: Session = Depends(get_db)):
    # 根据内容策划 ID 查询下游所有关联记录；旧数据没有关联字段时返回空数组。
    content_plan = db.query(ContentPlan).filter(ContentPlan.id == content_plan_id).first()
    scripts = db.query(ScriptPolish).filter(ScriptPolish.content_plan_id == content_plan_id).order_by(ScriptPolish.created_at.desc()).all()
    storyboards = db.query(Storyboard).filter(Storyboard.content_plan_id == content_plan_id).order_by(Storyboard.created_at.desc()).all()
    localizations = db.query(Localization).filter(Localization.content_plan_id == content_plan_id).order_by(Localization.created_at.desc()).all()
    ads = db.query(AdMaterial).filter(AdMaterial.content_plan_id == content_plan_id).order_by(AdMaterial.created_at.desc()).all()

    return {
        "code": 0,
        "message": "success",
        "data": {
            "contentPlan": content_plan_item(content_plan),
            "scriptPolishes": [script_item(item) for item in scripts],
            "storyboards": [storyboard_item(item) for item in storyboards],
            "localizations": [localization_item(item) for item in localizations],
            "adMaterials": [ad_item(item) for item in ads],
        },
    }
