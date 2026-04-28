import json
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.localization import Localization
from app.models.short_drama_episode import ShortDramaEpisode
from app.services.ai_service import generate_json
from app.services.project_flow import advance_project_stage


router = APIRouter(prefix="/localization")

SYSTEM_PROMPT = (
    "你是一个 AI短剧内容生产助手，擅长短剧内容策划、剧本打磨、分镜拆解、多语种本地化和海外广告投放素材生成。"
    "你必须严格返回 JSON 对象，不要返回 Markdown，不要解释，不要代码块。"
)


class LocalizationProcessRequest(BaseModel):
    # 本地化处理请求：市场、语言和策略影响改写风格。
    market: str
    language: str
    strategy: str
    project_id: Optional[int] = None
    episode_id: Optional[int] = None
    episode_no: Optional[int] = None
    contentPlanId: Optional[int] = None
    scriptPolishId: Optional[int] = None
    storyboardId: Optional[int] = None


def build_localization_result(payload: LocalizationProcessRequest) -> dict:
    subtitles = [
        {
            "index": 1,
            "startTime": "00:00.0",
            "endTime": "00:03.2",
            "originalText": "你怎么能这样对我？",
            "directTranslation": "How could you do this to me?",
            "localizedText": "After everything I gave up for you, this is how you repay me?",
            "voiceStatus": "已配音",
            "lipSyncStatus": "已匹配",
            "subtitleStatus": "已完成",
        },
        {
            "index": 2,
            "startTime": "00:03.2",
            "endTime": "00:07.5",
            "originalText": "我不是来求你们的。",
            "directTranslation": "I am not here to beg you.",
            "localizedText": "I did not come here for approval. I came here to end this.",
            "voiceStatus": "已配音",
            "lipSyncStatus": "已匹配",
            "subtitleStatus": "已完成",
        },
        {
            "index": 3,
            "startTime": "00:07.5",
            "endTime": "00:12.0",
            "originalText": "属于我的，我会亲手拿回来。",
            "directTranslation": "I will take back what belongs to me.",
            "localizedText": "Everything you stole from me starts coming back tonight.",
            "voiceStatus": "未配音",
            "lipSyncStatus": "未匹配",
            "subtitleStatus": "待处理",
        },
    ]
    workflow = [
        {"step": "提取原字幕", "status": "已完成", "description": "完成中文对白切分和时间轴识别。"},
        {"step": "AI翻译", "status": "已完成", "description": f"生成{payload.language}直译版本，保留基本语义。"},
        {"step": "本地化改写", "status": "已完成", "description": f"按{payload.strategy}策略强化海外表达。"},
        {"step": "AI配音", "status": "处理中", "description": "为核心对白生成目标语言配音。"},
        {"step": "口型匹配", "status": "处理中", "description": "根据配音节奏调整口型匹配状态。"},
        {"step": "字幕校对", "status": "待处理", "description": "等待人工或 AI 二次校对字幕风格。"},
        {"step": "导出海外版本", "status": "待处理", "description": f"准备导出面向{payload.market}的发布版本。"},
    ]
    return {
        "market": payload.market,
        "language": payload.language,
        "strategy": payload.strategy,
        "subtitles": subtitles,
        "workflow": workflow,
    }


def build_user_prompt(payload: LocalizationProcessRequest) -> str:
    return f"""
请模拟 AI短剧本地化流程：
目标市场：{payload.market}
目标语言：{payload.language}
本地化策略：{payload.strategy}

要求：
1. 不是普通翻译，是本地化改写。
2. localizedText 要更适合目标市场短视频/短剧表达。
3. voiceStatus 只能使用：未配音 / 已配音。
4. lipSyncStatus 只能使用：未匹配 / 已匹配。
5. subtitleStatus 只能使用：待处理 / 已完成。
6. 只返回 JSON 对象，字段必须严格如下：
{{
  "market": "string",
  "language": "string",
  "strategy": "string",
  "subtitles": [
    {{
      "index": 1,
      "startTime": "string",
      "endTime": "string",
      "originalText": "string",
      "directTranslation": "string",
      "localizedText": "string",
      "voiceStatus": "未配音",
      "lipSyncStatus": "未匹配",
      "subtitleStatus": "待处理"
    }}
  ],
  "workflow": [{{"step": "string", "status": "string", "description": "string"}}]
}}
"""


@router.post("/process")
def process_localization(payload: LocalizationProcessRequest, db: Session = Depends(get_db)):
    fallback_data = build_localization_result(payload)
    result = generate_json(SYSTEM_PROMPT, build_user_prompt(payload), fallback_data)

    record = Localization(
        project_id=payload.project_id,
        episode_id=payload.episode_id,
        episode_no=payload.episode_no,
        content_plan_id=payload.contentPlanId,
        script_polish_id=payload.scriptPolishId,
        storyboard_id=payload.storyboardId,
        market=payload.market,
        language=payload.language,
        strategy=payload.strategy,
        result_json=json.dumps(result, ensure_ascii=False),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    # 本地化完成后进入素材制作阶段；阶段流转失败不影响本次生成结果返回。
    advance_project_stage(db, payload.project_id, "material")
    # 分集级本地化生产状态流转：本地化完成后，该集进入媒体制作阶段；失败不影响本次生成结果返回。
    if payload.episode_id:
        try:
            episode = db.query(ShortDramaEpisode).filter(ShortDramaEpisode.id == payload.episode_id).first()
            if episode:
                episode.localization_status = "completed"
                episode.stage = "media"
                episode.updated_at = datetime.now()
                db.commit()
        except Exception as exc:
            db.rollback()
            print(f"本地化完成后更新分集状态失败，已忽略：episode_id={payload.episode_id}, error={exc}")

    return {
        "code": 0,
        "message": "success",
        "data": {"recordId": record.id, "project_id": payload.project_id, "episode_id": payload.episode_id, "episode_no": payload.episode_no, **result},
    }


@router.get("/list")
def get_localization_history(
    project_id: Optional[int] = Query(default=None),
    episode_id: Optional[int] = Query(default=None),
    episode_no: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(Localization)
    if project_id:
        query = query.filter(Localization.project_id == project_id)
    if episode_id:
        query = query.filter(Localization.episode_id == episode_id)
    if episode_no:
        query = query.filter(Localization.episode_no == episode_no)
    records = query.order_by(Localization.created_at.desc()).limit(20).all()
    data = [
        {
            "id": item.id,
            "recordId": item.id,
            "project_id": item.project_id,
            "episode_id": item.episode_id,
            "episode_no": item.episode_no,
            "contentPlanId": item.content_plan_id,
            "scriptPolishId": item.script_polish_id,
            "storyboardId": item.storyboard_id,
            "market": item.market,
            "language": item.language,
            "strategy": item.strategy,
            "result": json.loads(item.result_json),
            "createdAt": item.created_at.isoformat(),
        }
        for item in records
    ]
    return {"code": 0, "message": "success", "data": data}
