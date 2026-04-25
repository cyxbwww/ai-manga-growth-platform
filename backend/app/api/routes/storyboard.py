import json
import time
from typing import Optional

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from openai import OpenAI
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import AI_API_KEY, AI_BASE_URL, AI_MAX_TOKENS, AI_MODEL, AI_PROVIDER, AI_TEMPERATURE, AI_TIMEOUT
from app.core.database import get_db
from app.models.storyboard import Storyboard
from app.services.ai_service import generate_json


router = APIRouter(prefix="/storyboard")

SYSTEM_PROMPT = "你是一个 AI漫剧出海内容生产助手。你必须严格返回 JSON 对象，不要返回 Markdown，不要解释，不要代码块。"


class StoryboardGenerateRequest(BaseModel):
    title: str
    script: str
    style: str
    sceneCount: int
    contentPlanId: Optional[int] = None
    scriptPolishId: Optional[int] = None


def build_scene(index: int, style: str, title: str) -> dict:
    # mock 分镜：用于普通生成和无 AI 时的流式 fallback。
    duration = "4秒" if index <= 2 else "5秒"
    zh = {
        "title": f"{title} 分镜 {index}",
        "scene": f"第{index}幕发生在高压对峙场景中，镜头聚焦主角与对手的情绪变化。",
        "characterAction": "主角从被动沉默转为主动出击，抬眼、停顿、亮出关键证据。",
        "dialogue": "主角：今天结束的不是婚礼，是你们的谎言。",
        "emotion": ["压迫", "震惊", "反击", "反转", "释放", "悬念", "决断", "追更"][(index - 1) % 8],
        "visualPrompt": f"{style}，竖屏漫剧分镜，第{index}幕，婚礼现场强冲突，主角冷静反击，电影级灯光，适合AI图片生成",
        "motionPrompt": f"镜头从对手嘲讽表情推进到主角抬眼，切到文件特写，{duration}，情绪从压迫转向反击",
        "consistencyPrompt": "保持女主黑色长发、冷静眼神、白色礼服一致；保持男主深色西装和婚礼场景一致",
    }
    target = {
        "language": "英文",
        "title": f"{title} storyboard scene {index}",
        "scene": f"Scene {index} takes place in a high-pressure confrontation.",
        "characterAction": "The heroine looks up, pauses, and reveals decisive evidence.",
        "dialogue": "Heroine: This wedding is not ending today. Your lies are.",
        "emotion": "comeback",
        "visualPrompt": f"{style}, vertical AI manga drama storyboard, scene {index}, intense wedding confrontation, cinematic lighting",
        "motionPrompt": f"Camera pushes from mockery to heroine's calm eyes, then document close-up, {duration}",
        "consistencyPrompt": "Keep heroine and male lead appearance consistent across all scenes.",
    }
    return {"sceneNo": index, "duration": duration, **zh, "status": "待生成", "bilingual": {"zh": zh, "target": target}}


def build_storyboard_result(payload: StoryboardGenerateRequest) -> dict:
    scene_count = max(1, min(payload.sceneCount, 8))
    return {
        "storyboardTitle": f"{payload.title} - AI分镜生产稿",
        "style": payload.style,
        "scenes": [build_scene(index, payload.style, payload.title) for index in range(1, scene_count + 1)],
    }


def build_user_prompt(payload: StoryboardGenerateRequest) -> str:
    return f"""
请把以下剧本拆解成可生产的 AI 漫剧分镜。
剧本标题：{payload.title}
剧本文本：{payload.script}
画面风格：{payload.style}
分镜数量：{payload.sceneCount}
要求：scenes 数量必须等于 {payload.sceneCount}；status 使用“待生成”；同时输出 bilingual.zh 和 bilingual.target。
只返回 JSON 对象，字段包含 storyboardTitle、style、scenes。
"""


def normalize_storyboard_result(result: dict, fallback_data: dict, scene_count: int) -> dict:
    scenes = result.get("scenes") if isinstance(result, dict) else None
    if not isinstance(scenes, list) or len(scenes) != scene_count:
        return fallback_data
    return result


def sse_event(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


def save_storyboard_record(payload: StoryboardGenerateRequest, result: dict, db: Session) -> Storyboard:
    # 保存当前分镜记录，并写入上游链路 ID。
    stored_result = dict(result)
    stored_result.pop("recordId", None)
    record = Storyboard(
        title=payload.title,
        script=payload.script,
        style=payload.style,
        scene_count=payload.sceneCount,
        content_plan_id=payload.contentPlanId,
        script_polish_id=payload.scriptPolishId,
        result_json=json.dumps(stored_result, ensure_ascii=False),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def stream_deepseek_storyboard(payload: StoryboardGenerateRequest, fallback_data: dict) -> dict:
    client = OpenAI(api_key=AI_API_KEY, base_url=AI_BASE_URL, timeout=AI_TIMEOUT)
    response = client.chat.completions.create(
        model=AI_MODEL,
        messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": build_user_prompt(payload)}],
        temperature=AI_TEMPERATURE,
        max_tokens=AI_MAX_TOKENS,
        response_format={"type": "json_object"},
        stream=True,
    )
    content = ""
    for chunk in response:
        delta = chunk.choices[0].delta.content
        if delta:
            content += delta
    return normalize_storyboard_result(json.loads(content), fallback_data, payload.sceneCount)


@router.post("/generate")
def generate_storyboard(payload: StoryboardGenerateRequest, db: Session = Depends(get_db)):
    fallback_data = build_storyboard_result(payload)
    ai_result = generate_json(SYSTEM_PROMPT, build_user_prompt(payload), fallback_data)
    result = normalize_storyboard_result(ai_result, fallback_data, payload.sceneCount)
    record = save_storyboard_record(payload, result, db)
    return {"code": 0, "message": "success", "data": {"recordId": record.id, **result}}


@router.post("/stream")
def stream_storyboard(payload: StoryboardGenerateRequest, db: Session = Depends(get_db)):
    fallback_data = build_storyboard_result(payload)

    def event_generator():
        yield sse_event({"type": "meta", "data": {"storyboardTitle": fallback_data["storyboardTitle"], "style": fallback_data["style"]}})
        result = fallback_data
        try:
            if AI_PROVIDER == "deepseek" and AI_API_KEY:
                result = stream_deepseek_storyboard(payload, fallback_data)
        except Exception as exc:
            print(f"DeepSeek 分镜流式生成失败，使用 mock fallback: {exc}")
            result = fallback_data
        for scene in result["scenes"]:
            yield sse_event({"type": "scene", "data": scene})
            time.sleep(0.3)
        record = save_storyboard_record(payload, result, db)
        yield sse_event({"type": "done", "data": {"recordId": record.id}})

    return StreamingResponse(event_generator(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.get("/list")
def get_storyboard_history(db: Session = Depends(get_db)):
    records = db.query(Storyboard).order_by(Storyboard.created_at.desc()).limit(20).all()
    data = [
        {
            "id": item.id,
            "recordId": item.id,
            "contentPlanId": item.content_plan_id,
            "scriptPolishId": item.script_polish_id,
            "title": item.title,
            "script": item.script,
            "style": item.style,
            "sceneCount": item.scene_count,
            "result": json.loads(item.result_json),
            "createdAt": item.created_at.isoformat(),
        }
        for item in records
    ]
    return {"code": 0, "message": "success", "data": data}
