import json

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.ad_material import AdMaterial
from app.services.ai_service import generate_json


router = APIRouter(prefix="/ads")

SYSTEM_PROMPT = (
    "你是一个 AI漫剧出海内容生产助手，擅长短剧内容策划、剧本打磨、分镜拆解、多语种本地化和海外广告投放素材生成。"
    "你必须严格返回 JSON 对象，不要返回 Markdown，不要解释，不要代码块。"
)

BILINGUAL_REQUIREMENT = (
    "请同时输出中文版本和目标语言版本。原始顶层字段使用中文版本。"
    "bilingual.zh 为中文版本。bilingual.target 为目标语言版本。不要只输出目标语言。"
)


class AdsGenerateRequest(BaseModel):
    # 广告素材请求：字段保持与前端投放素材页一致。
    projectName: str
    market: str
    platform: str
    contentType: str
    contentPlanId: Optional[int] = None
    scriptPolishId: Optional[int] = None
    storyboardId: Optional[int] = None
    localizationId: Optional[int] = None


def target_language_for_market(market: str) -> str:
    # 广告模块没有单独语言输入，按市场给一个默认目标语言，便于双语展示。
    mapping = {"北美": "英文", "东南亚": "英文", "日本": "日文", "韩国": "韩文", "中东": "阿拉伯语"}
    return mapping.get(market, "英文")


def build_copy_items(titles: list[str], hooks: list[str], copies: list[str]) -> list[dict]:
    return [
        {
            "id": index + 1,
            "title": titles[index],
            "hook": hooks[index],
            "copy": copies[index],
            "recommended": index == 0,
        }
        for index in range(min(len(titles), len(hooks), len(copies), 3))
    ]


def build_ads_result(payload: AdsGenerateRequest) -> dict:
    # mock 广告素材生成：顶层字段保留前端既有卡片对象结构，双语字段提供可切换展示。
    language = target_language_for_market(payload.market)
    zh_titles = [
        "她失去一切，直到真相被公开",
        f"{payload.projectName}：一场婚礼，一次彻底反击",
        "所有人都在笑她，下一秒合同出现了",
    ]
    zh_hooks = [
        "他们以为她毫无还手之力，第一份文件就让全场安静。",
        "婚礼进行到一半，她终于发现了背叛。",
        "她转身离开前三秒，整个房间都沉默了。",
    ]
    zh_copies = [
        f"一条适合 {payload.platform} 的{payload.contentType}素材：背叛、揭露、反击，节奏快到无法划走。",
        f"面向{payload.market}用户：强冲突、清晰反转、结尾一句话推动追更。",
        "最好的复仇不是争吵，而是在最合适的瞬间拿出证据。",
    ]
    target_titles = [
        "She lost everything... until the truth came out",
        f"{payload.projectName}: one wedding, one brutal comeback",
        "Everyone laughed at her. Then the contract appeared.",
    ]
    target_hooks = [
        "They thought she was powerless. The first document proved them wrong.",
        "In the middle of her wedding, she discovered the betrayal.",
        "Three seconds before she walked away, the whole room went silent.",
    ]
    target_copies = [
        f"A {payload.contentType} story built for {payload.platform}: betrayal, reveal, and a comeback you cannot skip.",
        f"For {payload.market} audiences: fast conflict, clean reveal, and a final line that pushes viewers to the next episode.",
        "The best revenge is not shouting. It is showing the proof at the perfect moment.",
    ]
    zh = {
        "titles": zh_titles,
        "hooks": zh_hooks,
        "copies": zh_copies,
        "cta": ["立即观看", "下一集见", "完整剧集见主页"],
        "coverPrompt": f"{payload.platform}竖屏短剧封面，{payload.contentType}，被背叛的女主手持合同，高对比情绪，清晰主体，适合AI封面生成",
        "abTestSuggestions": [
            "A组测试强冲突开场，B组测试身份反转开场，观察3秒留存差异。",
            f"{payload.market}市场优先测试短句标题，减少解释性信息。",
            f"{payload.platform}建议前3秒放大人物表情和证据特写，提高停留率。",
        ],
    }
    target = {
        "language": language,
        "titles": target_titles,
        "hooks": target_hooks,
        "copies": target_copies,
        "cta": ["Watch now", "See what happens next", "Full episode in bio"],
        "coverPrompt": (
            f"{payload.platform} vertical drama cover, {payload.contentType}, betrayed heroine holding contract, "
            "high contrast emotion, bold readable composition, premium short drama poster"
        ),
        "abTestSuggestions": [
            "Test a direct conflict opening against an identity-reveal opening and compare 3-second retention.",
            f"For {payload.market}, use short high-impact titles with minimal explanation.",
            f"On {payload.platform}, use facial close-ups and proof shots in the first three seconds.",
        ],
    }
    return {
        "projectName": payload.projectName,
        "market": payload.market,
        "platform": payload.platform,
        "contentType": payload.contentType,
        "titles": zh_titles,
        "hooks": zh_hooks,
        "copies": build_copy_items(zh_titles, zh_hooks, zh_copies),
        "cta": zh["cta"],
        "coverPrompt": zh["coverPrompt"],
        "abTestSuggestions": zh["abTestSuggestions"],
        "bilingual": {"zh": zh, "target": target},
    }


def build_user_prompt(payload: AdsGenerateRequest) -> str:
    language = target_language_for_market(payload.market)
    # 当前前端需要 copies 卡片对象数组，因此顶层 copies 保持原接口兼容，bilingual.copies 使用字符串数组。
    return f"""
请为 AI 漫剧出海生成海外短视频广告投放素材：
项目名称：{payload.projectName}
目标市场：{payload.market}
目标语言：{language}
投放平台：{payload.platform}
内容类型：{payload.contentType}

要求：
1. 适配 TikTok / Instagram Reels / YouTube Shorts。
2. hooks 必须强调前三秒。
3. 标题要有冲突、悬念、反转。
4. copies 要适合海外短视频广告投放。
5. coverPrompt 要能直接用于 AI 封面图生成。
6. {BILINGUAL_REQUIREMENT}
7. 只返回 JSON 对象，字段必须严格如下：
{{
  "projectName": "string",
  "market": "string",
  "platform": "string",
  "contentType": "string",
  "titles": ["string"],
  "hooks": ["string"],
  "copies": [
    {{"id": 1, "title": "string", "hook": "string", "copy": "string", "recommended": true}}
  ],
  "cta": ["string"],
  "coverPrompt": "string",
  "abTestSuggestions": ["string"],
  "bilingual": {{
    "zh": {{
      "titles": ["string"],
      "hooks": ["string"],
      "copies": ["string"],
      "cta": ["string"],
      "coverPrompt": "string",
      "abTestSuggestions": ["string"]
    }},
    "target": {{
      "language": "{language}",
      "titles": ["string"],
      "hooks": ["string"],
      "copies": ["string"],
      "cta": ["string"],
      "coverPrompt": "string",
      "abTestSuggestions": ["string"]
    }}
  }}
}}
"""


def normalize_ads_result(result: dict, fallback_data: dict) -> dict:
    # 兼容模型返回 copies: string[] 的情况，转换为前端既有卡片结构。
    copies = result.get("copies")
    titles = result.get("titles") if isinstance(result.get("titles"), list) else fallback_data["titles"]
    hooks = result.get("hooks") if isinstance(result.get("hooks"), list) else fallback_data["hooks"]
    if isinstance(copies, list) and copies and isinstance(copies[0], str):
        result["copies"] = [
            {
                "id": index + 1,
                "title": titles[index] if index < len(titles) else f"素材 {index + 1}",
                "hook": hooks[index] if index < len(hooks) else "",
                "copy": copy,
                "recommended": index == 0,
            }
            for index, copy in enumerate(copies[:3])
        ]
    if not isinstance(result.get("copies"), list):
        return fallback_data
    if not isinstance(result.get("bilingual"), dict):
        result["bilingual"] = fallback_data["bilingual"]
    return result


@router.post("/generate")
def generate_ads(payload: AdsGenerateRequest, db: Session = Depends(get_db)):
    fallback_data = build_ads_result(payload)
    ai_result = generate_json(SYSTEM_PROMPT, build_user_prompt(payload), fallback_data)
    result = normalize_ads_result(ai_result, fallback_data)

    record = AdMaterial(
        content_plan_id=payload.contentPlanId,
        script_polish_id=payload.scriptPolishId,
        storyboard_id=payload.storyboardId,
        localization_id=payload.localizationId,
        project_name=payload.projectName,
        market=payload.market,
        platform=payload.platform,
        content_type=payload.contentType,
        result_json=json.dumps(result, ensure_ascii=False),
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return {"code": 0, "message": "success", "data": {"recordId": record.id, **result}}


@router.get("/list")
def get_ad_material_history(db: Session = Depends(get_db)):
    records = db.query(AdMaterial).order_by(AdMaterial.created_at.desc()).limit(20).all()
    data = [
        {
            "id": item.id,
            "recordId": item.id,
            "contentPlanId": item.content_plan_id,
            "scriptPolishId": item.script_polish_id,
            "storyboardId": item.storyboard_id,
            "localizationId": item.localization_id,
            "projectName": item.project_name,
            "market": item.market,
            "platform": item.platform,
            "contentType": item.content_type,
            "result": json.loads(item.result_json),
            "createdAt": item.created_at.isoformat(),
        }
        for item in records
    ]
    return {"code": 0, "message": "success", "data": data}
