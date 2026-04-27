import json
import time
from typing import Any, Optional

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

SYSTEM_PROMPT = (
    "你是一个 AI漫剧出海内容生产助手，擅长把短剧剧本拆解为可生产的分镜数据。"
    "你必须严格返回 JSON 对象，不要返回 Markdown，不要解释，不要代码块。"
)

SCENE_TEXT_FIELDS = [
    "title",
    "scene",
    "characterAction",
    "dialogue",
    "emotion",
    "visualPrompt",
    "motionPrompt",
    "consistencyPrompt",
]


class StoryboardGenerateRequest(BaseModel):
    title: str
    script: str
    style: str
    sceneCount: int
    contentPlanId: Optional[int] = None
    scriptPolishId: Optional[int] = None


def text_or_empty(value: Any) -> str:
    return value if isinstance(value, str) else ""


def build_scene(index: int, style: str, title: str) -> dict:
    # mock fallback 也必须返回完整 bilingual 对象，保证前端切换语言时不会出现空白。
    duration = "4秒" if index <= 2 else "5秒"
    zh = {
        "title": f"{title} 分镜 {index}",
        "scene": f"第{index}幕发生在高压对峙场景中，镜头聚焦主角与对手的情绪变化。",
        "characterAction": "主角从被动沉默转为主动反击，抬眼、停顿、亮出关键证据。",
        "dialogue": "主角：今天结束的不是婚礼，是你们的谎言。",
        "emotion": ["压迫", "震惊", "反击", "反转", "释放", "悬念", "决断", "追更"][(index - 1) % 8],
        "visualPrompt": f"{style}，竖屏漫剧分镜，第{index}幕，婚礼现场强冲突，主角冷静反击，电影级灯光，适合AI图片生成",
        "motionPrompt": f"镜头从对手嘲讽表情推进到主角抬眼，切到文件特写，{duration}，情绪从压迫转向反击",
        "consistencyPrompt": "保持女主黑色长发、冷静眼神、白色礼服一致；保持男主深色西装和婚礼场景一致",
    }
    target = {
        "language": "英文",
        "title": f"{title} storyboard scene {index}",
        "scene": f"Scene {index} takes place in a high-pressure confrontation, focusing on the emotional shift between the heroine and her opponents.",
        "characterAction": "The heroine moves from silence to a decisive counterattack, raises her eyes, pauses, and reveals key evidence.",
        "dialogue": "Heroine: This wedding is not ending today. Your lies are.",
        "emotion": "comeback",
        "visualPrompt": f"{style}, vertical AI manga drama storyboard, scene {index}, intense wedding confrontation, calm heroine counterattack, cinematic lighting, suitable for AI image generation",
        "motionPrompt": f"Camera pushes from the opponent's mocking face to the heroine's calm eyes, then cuts to a document close-up, {duration}, emotion shifts from pressure to comeback",
        "consistencyPrompt": "Keep the heroine's long black hair, calm eyes, and white wedding dress consistent; keep the male lead's dark suit and wedding venue consistent.",
    }
    return {
        "sceneNo": index,
        "sceneNumber": index,
        "duration": duration,
        **zh,
        "status": "待生成",
        "bilingual": {"zh": zh, "target": target},
    }


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

必须返回 JSON 对象，顶层字段包含：
- storyboardTitle: string
- style: string
- scenes: array

每个 scene 必须包含以下字段：
- sceneNo: number
- sceneNumber: number
- title: string
- duration: string
- scene: string
- characterAction: string
- dialogue: string
- emotion: string
- visualPrompt: string
- motionPrompt: string
- consistencyPrompt: string
- status: "待生成"
- bilingual: object

重要要求：
1. scenes 数量必须等于 {payload.sceneCount}。
2. 顶层 title、scene、characterAction、dialogue、emotion、visualPrompt、motionPrompt、consistencyPrompt 默认使用中文版本。
3. 每个 scene 的 bilingual.zh 和 bilingual.target 必须是对象，不允许是字符串。
4. bilingual.zh 对象必须包含 title、scene、characterAction、dialogue、emotion、visualPrompt、motionPrompt、consistencyPrompt。
5. bilingual.target 对象必须包含 language、title、scene、characterAction、dialogue、emotion、visualPrompt、motionPrompt、consistencyPrompt。
6. visualPrompt 要能直接用于 AI 图片生成。
7. motionPrompt 要能直接用于图生视频。
8. consistencyPrompt 用于保证角色一致性。
9. 只返回 JSON 对象，不要返回 Markdown，不要解释，不要代码块。
"""


def normalize_bilingual_value(value: Any, scene: dict, scene_no: int, language: str | None = None) -> dict:
    # AI 有时会把 bilingual.zh / target 返回成字符串，这里统一转换为完整对象，避免前端字段为空。
    if isinstance(value, dict):
        source = value
        scene_text = text_or_empty(source.get("scene"))
    elif isinstance(value, str):
        source = {}
        scene_text = value
    else:
        source = {}
        scene_text = ""

    normalized = {
        "title": text_or_empty(source.get("title")) or text_or_empty(scene.get("title")) or f"分镜{scene_no}",
        "scene": scene_text or text_or_empty(scene.get("scene")),
        "characterAction": text_or_empty(source.get("characterAction")) or text_or_empty(scene.get("characterAction")),
        "dialogue": text_or_empty(source.get("dialogue")) or text_or_empty(scene.get("dialogue")),
        "emotion": text_or_empty(source.get("emotion")) or text_or_empty(scene.get("emotion")),
        "visualPrompt": text_or_empty(source.get("visualPrompt")) or text_or_empty(scene.get("visualPrompt")),
        "motionPrompt": text_or_empty(source.get("motionPrompt")) or text_or_empty(scene.get("motionPrompt")),
        "consistencyPrompt": text_or_empty(source.get("consistencyPrompt")) or text_or_empty(scene.get("consistencyPrompt")),
    }
    if language is not None:
        normalized["language"] = text_or_empty(source.get("language")) or language
    return normalized


def normalize_scene(scene: Any, index: int, fallback_scene: dict) -> dict:
    # 统一 sceneNo / sceneNumber，并保证顶层字段、bilingual.zh、bilingual.target 都是完整结构。
    if not isinstance(scene, dict):
        scene = {}

    scene_no = scene.get("sceneNo") or scene.get("sceneNumber") or index
    try:
        scene_no = int(scene_no)
    except Exception:
        scene_no = index

    merged = {**fallback_scene, **scene}
    merged["sceneNo"] = scene_no
    merged["sceneNumber"] = scene_no
    merged["duration"] = text_or_empty(merged.get("duration")) or text_or_empty(fallback_scene.get("duration")) or "4秒"
    merged["status"] = text_or_empty(merged.get("status")) or "待生成"

    bilingual = merged.get("bilingual") if isinstance(merged.get("bilingual"), dict) else {}
    zh = normalize_bilingual_value(bilingual.get("zh"), merged, scene_no)
    target = normalize_bilingual_value(bilingual.get("target"), merged, scene_no, "目标语言")

    # 顶层字段默认使用中文版本，方便中文页面和旧逻辑直接展示。
    for field in SCENE_TEXT_FIELDS:
        merged[field] = zh[field] or text_or_empty(fallback_scene.get(field))

    merged["bilingual"] = {"zh": zh, "target": target}
    return merged


def normalize_storyboard_result(result: dict, fallback_data: dict, scene_count: int) -> dict:
    # 不信任 AI 原始结构：到前端前强制补齐 scenes 数量和每个 scene 的 bilingual 对象字段。
    if not isinstance(result, dict):
        result = {}

    fallback_scenes = fallback_data["scenes"]
    raw_scenes = result.get("scenes")
    if not isinstance(raw_scenes, list):
        raw_scenes = []

    normalized_scenes = []
    for index in range(1, scene_count + 1):
        raw_scene = raw_scenes[index - 1] if index - 1 < len(raw_scenes) else {}
        fallback_scene = fallback_scenes[index - 1] if index - 1 < len(fallback_scenes) else build_scene(index, fallback_data["style"], fallback_data["storyboardTitle"])
        normalized_scenes.append(normalize_scene(raw_scene, index, fallback_scene))

    return {
        "storyboardTitle": text_or_empty(result.get("storyboardTitle")) or fallback_data["storyboardTitle"],
        "style": text_or_empty(result.get("style")) or fallback_data["style"],
        "scenes": normalized_scenes,
    }


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
        result = normalize_storyboard_result(result, fallback_data, payload.sceneCount)
        for scene in result["scenes"]:
            yield sse_event({"type": "scene", "data": scene})
            time.sleep(0.3)
        record = save_storyboard_record(payload, result, db)
        yield sse_event({"type": "done", "data": {"recordId": record.id}})

    return StreamingResponse(event_generator(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.get("/list")
def get_storyboard_history(db: Session = Depends(get_db)):
    records = db.query(Storyboard).order_by(Storyboard.created_at.desc()).limit(20).all()
    data = []
    for item in records:
        fallback_payload = StoryboardGenerateRequest(title=item.title, script=item.script, style=item.style, sceneCount=item.scene_count)
        fallback_data = build_storyboard_result(fallback_payload)
        try:
            raw_result = json.loads(item.result_json)
        except Exception:
            raw_result = fallback_data
        # 历史记录可能保存的是旧结构，这里复用生成接口的归一化逻辑，保证前端点击历史也不会空白。
        result = normalize_storyboard_result(raw_result, fallback_data, item.scene_count)
        data.append(
            {
                "id": item.id,
                "recordId": item.id,
                "contentPlanId": item.content_plan_id,
                "scriptPolishId": item.script_polish_id,
                "title": item.title,
                "script": item.script,
                "style": item.style,
                "sceneCount": item.scene_count,
                "result": result,
                "createdAt": item.created_at.isoformat(),
            }
        )
    return {"code": 0, "message": "success", "data": data}
