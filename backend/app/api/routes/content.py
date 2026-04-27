import json

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.content_plan import ContentPlan
from app.services.ai_service import generate_json


router = APIRouter(prefix="/content")

SYSTEM_PROMPT = (
    "你是一个 AI短剧内容生产助手，擅长短剧内容策划、剧本打磨、分镜拆解、多语种本地化和海外广告投放素材生成。"
    "你必须严格返回 JSON 对象，不要返回 Markdown，不要解释，不要代码块。"
)

BILINGUAL_REQUIREMENT = (
    "请同时输出中文版本和目标语言版本。原始顶层字段使用中文版本。"
    "bilingual.zh 为中文版本。bilingual.target 为目标语言版本。不要只输出目标语言。"
)


class ContentPlanRequest(BaseModel):
    # 内容策划请求：字段保持与前端和历史版本接口兼容。
    projectName: str
    genre: str
    market: str
    language: str
    duration: str
    sellingPoint: str


def build_content_plan_result(payload: ContentPlanRequest) -> dict:
    # mock 兜底也返回双语结构，保证 DeepSeek 未配置或失败时前端语言切换仍可用。
    zh = {
        "title": f"{payload.projectName} - {payload.market}{payload.duration}短剧策划",
        "positioning": f"面向{payload.market}市场的{payload.genre}竖屏短剧，默认使用中文做内部审核，再输出{payload.language}用于海外投放。",
        "targetAudience": "18-34岁短视频用户，偏好强情绪、快反转、明确爽点和可快速理解的人物关系。",
        "coreConflict": "主角在亲密关系或身份关系中被低估，随后用隐藏资源完成反击，形成压迫到逆转的强对比。",
        "emotionHook": "用背叛、羞辱、误解或错失制造情绪压力，再用身份揭晓和主动反击释放情绪。",
        "openingHook": "开场3秒直接给出冲突现场：主角被当众否定，同时抛出一句带身份反转的信息。",
        "highlights": [
            "爽点：弱势主角亮出隐藏身份或关键证据",
            "泪点：主角短暂回忆被家人或恋人抛弃的瞬间",
            "反转点：观众以为主角失败，实际她早已掌握主动权",
        ],
        "platforms": ["TikTok", "YouTube Shorts", "Instagram Reels"],
        "suggestions": [
            f"{payload.duration}版本建议控制在一个核心冲突内，避免支线过多。",
            f"{payload.market}市场表达要减少解释性台词，优先使用动作和结果呈现人物关系。",
            f"核心卖点可落地为：{payload.sellingPoint[:36]}，并在结尾设置追更悬念。",
        ],
    }
    target = {
        "language": payload.language,
        "title": f"{payload.projectName} - {payload.market} {payload.duration} overseas drama plan",
        "positioning": f"A vertical AI manga drama for the {payload.market} market, localized in {payload.language} with a clear first-3-second hook.",
        "targetAudience": "Short-video viewers aged 18-34 who respond to high emotion, quick reversals, and clear character stakes.",
        "coreConflict": "The heroine is publicly underestimated, then uses hidden leverage to turn humiliation into a powerful comeback.",
        "emotionHook": "Open with betrayal and public pressure, then release emotion through a reveal, proof, and decisive action.",
        "openingHook": "Start with a public rejection in the first three seconds, followed by one line that hints at a hidden identity.",
        "highlights": [
            "Payoff: the weak-looking heroine reveals proof or hidden power",
            "Tear point: a short memory of being abandoned by family or lover",
            "Twist: the audience thinks she lost, but she has controlled the situation all along",
        ],
        "platforms": ["TikTok", "YouTube Shorts", "Instagram Reels"],
        "suggestions": [
            "Keep one main conflict in the short version and avoid too many side plots.",
            "Use actions and visible outcomes instead of long explanatory dialogue.",
            "End with a strong cliffhanger that can lead into storyboard and ad material production.",
        ],
    }
    return {**zh, "bilingual": {"zh": zh, "target": target}}


def build_user_prompt(payload: ContentPlanRequest) -> str:
    # Prompt 明确双语 JSON 结构，避免目标语言覆盖内部审核所需中文内容。
    return f"""
请根据以下用户输入生成 AI短剧内容策划方案。
项目名称：{payload.projectName}
短剧题材：{payload.genre}
目标市场：{payload.market}
目标语言：{payload.language}
视频时长：{payload.duration}
核心卖点：{payload.sellingPoint}

要求：
1. 适合 AI短剧，结果适合后续分镜制作和广告投放。
2. 根据目标市场做内容定位。
3. 强调前三秒钩子、冲突、反转和情绪价值。
4. {BILINGUAL_REQUIREMENT}
5. 只返回 JSON 对象，字段必须严格如下：
{{
  "title": "string",
  "positioning": "string",
  "targetAudience": "string",
  "coreConflict": "string",
  "emotionHook": "string",
  "openingHook": "string",
  "highlights": ["string"],
  "platforms": ["string"],
  "suggestions": ["string"],
  "bilingual": {{
    "zh": {{
      "title": "string",
      "positioning": "string",
      "targetAudience": "string",
      "coreConflict": "string",
      "emotionHook": "string",
      "openingHook": "string",
      "highlights": ["string"],
      "platforms": ["string"],
      "suggestions": ["string"]
    }},
    "target": {{
      "language": "{payload.language}",
      "title": "string",
      "positioning": "string",
      "targetAudience": "string",
      "coreConflict": "string",
      "emotionHook": "string",
      "openingHook": "string",
      "highlights": ["string"],
      "platforms": ["string"],
      "suggestions": ["string"]
    }}
  }}
}}
"""


@router.post("/plan")
def create_content_plan(payload: ContentPlanRequest, db: Session = Depends(get_db)):
    fallback_data = build_content_plan_result(payload)
    result = generate_json(SYSTEM_PROMPT, build_user_prompt(payload), fallback_data)

    # 无论 DeepSeek 还是 fallback，最终结果都写入 SQLite。
    record = ContentPlan(
        project_name=payload.projectName,
        genre=payload.genre,
        market=payload.market,
        language=payload.language,
        duration=payload.duration,
        selling_point=payload.sellingPoint,
        result_json=json.dumps(result, ensure_ascii=False),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return {"code": 0, "message": "success", "data": {"recordId": record.id, **result}}


@router.get("/plans")
def get_content_plan_history(db: Session = Depends(get_db)):
    # 历史记录：最近 20 条，按创建时间倒序返回。
    records = db.query(ContentPlan).order_by(ContentPlan.created_at.desc()).limit(20).all()
    data = [
        {
            "id": item.id,
            "recordId": item.id,
            "projectName": item.project_name,
            "genre": item.genre,
            "market": item.market,
            "language": item.language,
            "duration": item.duration,
            "sellingPoint": item.selling_point,
            "result": json.loads(item.result_json),
            "createdAt": item.created_at.isoformat(),
        }
        for item in records
    ]
    return {"code": 0, "message": "success", "data": data}
