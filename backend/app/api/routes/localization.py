import json
import re
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.localization import Localization
from app.models.short_drama_episode import ShortDramaEpisode
from app.models.short_drama_project import ShortDramaProject
from app.services.ai_service import generate_json
from app.services.project_flow import advance_project_stage


router = APIRouter(prefix="/localization")

SYSTEM_PROMPT = (
    "你是一个 AI短剧内容生产助手，擅长短剧内容策划、剧本打磨、分镜拆解、多语种本地化和海外广告投放素材生成。"
    "你必须严格返回 JSON 对象，不要返回 Markdown，不要解释，不要代码块。"
)


class LocalizationProcessRequest(BaseModel):
    # 同时兼容新前端 camelCase 和旧接口 snake_case，避免历史页面调用失效。
    projectId: Optional[int] = None
    episodeId: Optional[int] = None
    episodeNo: Optional[int] = None
    sourceText: Optional[str] = None
    targetMarket: Optional[str] = None
    targetLanguage: Optional[str] = None
    strategy: str
    market: Optional[str] = None
    language: Optional[str] = None
    source_text: Optional[str] = None
    project_id: Optional[int] = None
    episode_id: Optional[int] = None
    episode_no: Optional[int] = None
    contentPlanId: Optional[int] = None
    scriptPolishId: Optional[int] = None
    storyboardId: Optional[int] = None


def normalized_payload(payload: LocalizationProcessRequest) -> dict:
    return {
        "project_id": payload.projectId or payload.project_id,
        "episode_id": payload.episodeId or payload.episode_id,
        "episode_no": payload.episodeNo or payload.episode_no,
        "source_text": (payload.sourceText or payload.source_text or "").strip(),
        "market": (payload.targetMarket or payload.market or "").strip(),
        "language": (payload.targetLanguage or payload.language or "").strip(),
        "strategy": payload.strategy,
    }


def split_source_text(source_text: str) -> list[str]:
    # mock fallback 也必须吃用户输入：优先按换行切分，长段落再按中文/英文标点拆成字幕。
    lines = [line.strip() for line in source_text.splitlines() if line.strip()]
    if len(lines) <= 1:
        lines = [item.strip() for item in re.split(r"(?<=[。！？!?；;])\s*", source_text) if item.strip()]
    return lines[:8] or [source_text]


def build_localized_mock_line(text: str, market: str, language: str, strategy: str) -> str:
    return f"{language} 本地化稿（{market} / {strategy}）：{text}"


def build_workflow(market: str, language: str, strategy: str) -> list[dict]:
    workflow = [
        {"step": "提取原字幕", "status": "已完成", "description": "已基于当前输入剧本文本切分字幕。"},
        {"step": "AI翻译", "status": "已完成", "description": f"生成{language}直译草稿，保留原剧情含义。"},
        {"step": "本地化改写", "status": "已完成", "description": f"按{strategy}策略适配{market}文化语境。"},
        {"step": "AI配音", "status": "处理中", "description": "为核心对白生成目标语言配音。"},
        {"step": "口型匹配", "status": "处理中", "description": "根据配音节奏调整口型匹配状态。"},
        {"step": "字幕校对", "status": "待处理", "description": "等待人工或 AI 二次校对字幕风格。"},
        {"step": "导出海外版本", "status": "待处理", "description": f"准备导出面向{market}的发布版本。"},
    ]
    return workflow


def build_localization_result(payload: LocalizationProcessRequest) -> dict:
    normalized = normalized_payload(payload)
    source_text = normalized["source_text"]
    market = normalized["market"]
    language = normalized["language"]
    strategy = normalized["strategy"]
    subtitles = []
    for index, text in enumerate(split_source_text(source_text), start=1):
        start_seconds = (index - 1) * 4
        end_seconds = start_seconds + 4
        subtitles.append(
            {
                "index": index,
                "startTime": f"00:{start_seconds:02d}.0",
                "endTime": f"00:{end_seconds:02d}.0",
                "originalText": text,
                "directTranslation": f"{language} 直译草稿：{text}",
                "localizedText": build_localized_mock_line(text, market, language, strategy),
                "voiceStatus": "已配音" if index <= 2 else "未配音",
                "lipSyncStatus": "已匹配" if index <= 2 else "未匹配",
                "subtitleStatus": "已完成" if index <= 2 else "待处理",
            }
        )
    workflow = build_workflow(market, language, strategy)
    return {
        "sourceText": source_text,
        "targetMarket": market,
        "targetLanguage": language,
        "market": market,
        "language": language,
        "strategy": strategy,
        "subtitles": subtitles,
        "comparison": [
            {
                "originalText": subtitles[0]["originalText"],
                "directTranslation": subtitles[0]["directTranslation"],
                "localizedText": subtitles[0]["localizedText"],
            }
        ],
        "workflowSteps": workflow,
        "workflow": workflow,
        "status": "completed",
    }


def normalize_ai_result(result: dict, fallback_data: dict) -> dict:
    data = {**fallback_data, **(result or {})}
    data["subtitles"] = data.get("subtitles") or fallback_data["subtitles"]
    data["comparison"] = data.get("comparison") or [
        {
            "originalText": data["subtitles"][0].get("originalText", ""),
            "directTranslation": data["subtitles"][0].get("directTranslation", ""),
            "localizedText": data["subtitles"][0].get("localizedText", ""),
        }
    ]
    workflow = data.get("workflowSteps") or data.get("workflow") or fallback_data["workflowSteps"]
    data["workflowSteps"] = workflow
    data["workflow"] = workflow
    data["status"] = data.get("status") or "completed"
    return data


def build_user_prompt(payload: LocalizationProcessRequest, project: ShortDramaProject, episode: ShortDramaEpisode) -> str:
    normalized = normalized_payload(payload)
    return f"""
请模拟 AI短剧本地化流程：
剧情背景：
项目名称：{project.name}
项目类型：{project.genre}
项目简介：{project.description or "暂无"}

当前分集内容：
第 {episode.episode_no} 集：{episode.title}
分集大纲：{episode.summary or "暂无"}

原始台词/字幕：
{normalized["source_text"]}

目标市场：{normalized["market"]}
目标语言：{normalized["language"]}
本地化策略：{normalized["strategy"]}

要求：
1. 本地化不是逐字翻译，而是基于剧情语境的文化适配。
2. 必须保留原剧情含义。
3. 可以增强情绪表达，但不能新增无关剧情。
4. voiceStatus 只能使用：未配音 / 已配音。
5. lipSyncStatus 只能使用：未匹配 / 已匹配。
6. subtitleStatus 只能使用：待处理 / 已完成。
7. 只返回 JSON 对象，字段必须严格如下：
{{
  "market": "string",
  "language": "string",
  "targetMarket": "string",
  "targetLanguage": "string",
  "sourceText": "string",
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
  "comparison": [{{"originalText": "string", "directTranslation": "string", "localizedText": "string"}}],
  "workflowSteps": [{{"step": "string", "status": "string", "description": "string"}}],
  "status": "completed"
}}
"""


@router.post("/process")
def process_localization(payload: LocalizationProcessRequest, db: Session = Depends(get_db)):
    normalized = normalized_payload(payload)
    if not normalized["project_id"] or not normalized["episode_id"]:
        raise HTTPException(status_code=400, detail="请先选择项目和分集")
    if not normalized["source_text"]:
        raise HTTPException(status_code=400, detail="请先输入需要本地化的剧本文本")
    project = db.query(ShortDramaProject).filter(ShortDramaProject.id == normalized["project_id"]).first()
    if not project:
        raise HTTPException(status_code=404, detail="项目不存在")
    episode = db.query(ShortDramaEpisode).filter(ShortDramaEpisode.id == normalized["episode_id"]).first()
    if not episode:
        raise HTTPException(status_code=404, detail="分集不存在")
    if episode.project_id != project.id:
        raise HTTPException(status_code=400, detail="分集不属于当前项目")

    fallback_data = build_localization_result(payload)
    result = normalize_ai_result(generate_json(SYSTEM_PROMPT, build_user_prompt(payload, project, episode), fallback_data), fallback_data)

    record = Localization(
        project_id=normalized["project_id"],
        episode_id=normalized["episode_id"],
        episode_no=normalized["episode_no"] or episode.episode_no,
        content_plan_id=payload.contentPlanId,
        script_polish_id=payload.scriptPolishId,
        storyboard_id=payload.storyboardId,
        market=normalized["market"],
        language=normalized["language"],
        strategy=normalized["strategy"],
        result_json=json.dumps(result, ensure_ascii=False),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    # 本地化完成后进入素材制作阶段；阶段流转失败不影响本次生成结果返回。
    advance_project_stage(db, normalized["project_id"], "material")
    # 分集级本地化生产状态流转：本地化完成后，该集进入媒体制作阶段；失败不影响本次生成结果返回。
    if normalized["episode_id"]:
        try:
            episode.localization_status = "completed"
            episode.stage = "media"
            episode.updated_at = datetime.now()
            db.commit()
        except Exception as exc:
            db.rollback()
            print(f"本地化完成后更新分集状态失败，已忽略：episode_id={normalized['episode_id']}, error={exc}")

    return {
        "code": 0,
        "message": "success",
        "data": {
            "recordId": record.id,
            "projectId": normalized["project_id"],
            "episodeId": normalized["episode_id"],
            "episodeNo": normalized["episode_no"] or episode.episode_no,
            "project_id": normalized["project_id"],
            "episode_id": normalized["episode_id"],
            "episode_no": normalized["episode_no"] or episode.episode_no,
            **result,
        },
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
            "targetMarket": item.market,
            "targetLanguage": item.language,
            "strategy": item.strategy,
            "result": json.loads(item.result_json),
            "createdAt": item.created_at.isoformat(),
        }
        for item in records
    ]
    return {"code": 0, "message": "success", "data": data}
