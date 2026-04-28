import json

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.script_polish import ScriptPolish
from app.services.ai_service import generate_json
from app.services.dictionary_service import language_prompt_name, normalize_language_code
from app.services.project_flow import advance_project_stage


router = APIRouter(prefix="/script")

SYSTEM_PROMPT = (
    "你是一个 AI短剧内容生产助手，擅长短剧内容策划、剧本打磨、分镜拆解、多语种本地化和海外广告投放素材生成。"
    "你必须严格返回 JSON 对象，不要返回 Markdown，不要解释，不要代码块。"
)

BILINGUAL_REQUIREMENT = (
    "请同时输出中文版本和目标语言版本。原始顶层字段使用中文版本。"
    "bilingual.zh 为中文版本。bilingual.target 为目标语言版本。不要只输出目标语言。"
)


class ScriptPolishRequest(BaseModel):
    # 剧本打磨请求：directions 为用户选择的优化方向。
    project_id: Optional[int] = None
    title: str
    script: str
    directions: list[str]
    contentPlanId: Optional[int] = None
    # language 保存和传递字典 value，例如 en-US；Prompt 中再临时转成中文语言名。
    language: Optional[str] = None
    target_language: Optional[str] = None


def build_script_polish_result(payload: ScriptPolishRequest) -> dict:
    # mock 打磨逻辑：原字段保留中文，bilingual.target 预留给海外投放表达。
    language_code = script_language_code(payload)
    language_name = language_prompt_name(language_code)
    directions_text = "、".join(payload.directions) if payload.directions else "基础节奏优化"
    zh_polished = (
        f"《{payload.title}》优化片段\n"
        "【0-3秒】婚礼现场，大屏突然亮起股权转让文件。继妹冷笑：'你连自己的公司都保不住，还想嫁进来？'\n"
        "【3-10秒】女主抬眼，没有解释，只把戒指放在桌上：'谢谢你们提醒我，今天该签的不是婚约。'\n"
        "【10-20秒】律师推门而入，宣布最终控股人仍是女主。未婚夫脸色骤变，全场安静。\n"
        "【结尾钩子】女主转身离开：'下一集，我会拿回属于我的一切。'"
    )
    zh_tips = [
        f"本次重点方向：{directions_text}。",
        "把解释性台词改为证据、动作和结果，让短视频用户更快理解冲突。",
        "每15-20秒设置一次信息反转，保证短剧片段具备追更动力。",
        "海外版本避免过度依赖亲属称谓，优先突出权利关系、背叛和选择。",
    ]
    target_polished = (
        f"{payload.title} - localized polished excerpt\n"
        "[0-3s] At the wedding, a share transfer document appears on the big screen. The stepsister says, 'You could not even keep your company. Why would he marry you?'\n"
        "[3-10s] The heroine stays calm, places the ring on the table, and says, 'Thanks for the reminder. The contract I sign today is not a marriage contract.'\n"
        "[10-20s] Her lawyer walks in and confirms she is still the controlling shareholder. The room goes silent.\n"
        "[Cliffhanger] She walks away: 'Next episode, I take back everything they stole.'"
    )
    target_tips = [
        "Make the first line feel like a challenge, not an explanation.",
        "Use proof, status reversal, and silence to create a stronger short-drama payoff.",
        "Keep the overseas copy direct: betrayal, contract, control, comeback.",
    ]
    return {
        "score": 86,
        "diagnostics": [
            {
                "type": "前三秒钩子",
                "problem": "原稿进入冲突较快，但缺少一句能立刻制造停留的信息差台词。",
                "suggestion": "开头直接放大背叛现场，并加入身份或证据反转的暗示。",
            },
            {
                "type": "冲突强度",
                "problem": "对手压迫感可以更明确，让观众快速站队主角。",
                "suggestion": "增加公开羞辱或利益剥夺动作，压缩铺垫时间。",
            },
            {
                "type": "海外表达",
                "problem": "部分中文语境下的家族和面子表达，需要转成更直接的权利、契约和选择。",
                "suggestion": "用 contract、control、walk away 等更易跨文化理解的表达承接情绪。",
            },
        ],
        "polishedScript": zh_polished,
        "localizedRewrite": [
            {
                "original": "你们欠我的，我都会拿回来。",
                "directTranslation": "I will take back everything you owe me.",
                "localizedVersion": "Everything you stole from me starts coming back tonight.",
            },
            {
                "original": "我不是来求你们的。",
                "directTranslation": "I am not here to beg you.",
                "localizedVersion": "I did not come here for approval. I came here to end this.",
            },
        ],
        "optimizationTips": zh_tips,
        "bilingual": {
            "zh": {"polishedScript": zh_polished, "optimizationTips": zh_tips},
            "target": {"language": language_name, "polishedScript": target_polished, "optimizationTips": target_tips},
        },
    }


def script_language_code(payload: ScriptPolishRequest) -> str:
    return normalize_language_code(payload.language or payload.target_language) or "en-US"


def infer_language_from_result(result: dict) -> str:
    target_language = None
    bilingual = result.get("bilingual") if isinstance(result, dict) else None
    if isinstance(bilingual, dict) and isinstance(bilingual.get("target"), dict):
        target_language = bilingual["target"].get("language")
    return normalize_language_code(target_language) or "en-US"


def build_user_prompt(payload: ScriptPolishRequest) -> str:
    # 主存储字段使用语言 code；Prompt 临时转成中文语言名，便于模型理解目标表达。
    language_code = script_language_code(payload)
    language_name = language_prompt_name(language_code)
    return f"""
请对以下 AI短剧剧本进行精品化打磨：
剧本标题：{payload.title}
原始剧本：{payload.script}
打磨方向：{json.dumps(payload.directions, ensure_ascii=False)}
目标语言：{language_name}

要求：
1. 诊断节奏、冲突、反转、情绪张力。
2. 强化前三秒钩子，优化海外表达。
3. localizedVersion 不能只是直译，要像海外短剧投放文案一样改写。
4. {BILINGUAL_REQUIREMENT}
5. 只返回 JSON 对象，字段必须严格如下：
{{
  "score": 0,
  "diagnostics": [{{"type": "string", "problem": "string", "suggestion": "string"}}],
  "polishedScript": "string",
  "localizedRewrite": [{{"original": "string", "directTranslation": "string", "localizedVersion": "string"}}],
  "optimizationTips": ["string"],
  "bilingual": {{
    "zh": {{"polishedScript": "string", "optimizationTips": ["string"]}},
    "target": {{"language": "{language_name}", "polishedScript": "string", "optimizationTips": ["string"]}}
  }}
}}
"""


@router.post("/polish")
def polish_script(payload: ScriptPolishRequest, db: Session = Depends(get_db)):
    language_code = script_language_code(payload)
    fallback_data = build_script_polish_result(payload)
    result = generate_json(SYSTEM_PROMPT, build_user_prompt(payload), fallback_data)

    record = ScriptPolish(
        project_id=payload.project_id,
        content_plan_id=payload.contentPlanId,
        language=language_code,
        title=payload.title,
        original_script=payload.script,
        directions_json=json.dumps(payload.directions, ensure_ascii=False),
        result_json=json.dumps(result, ensure_ascii=False),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    advance_project_stage(db, payload.project_id, "storyboard")

    return {
        "code": 0,
        "message": "success",
        "data": {
            "recordId": record.id,
            "project_id": payload.project_id,
            "language": language_code,
            "target_language": language_code,
            **result,
        },
    }


@router.get("/polishes")
def get_script_polish_history(db: Session = Depends(get_db)):
    records = db.query(ScriptPolish).order_by(ScriptPolish.created_at.desc()).limit(20).all()
    data = []
    for item in records:
        result = json.loads(item.result_json)
        language_code = normalize_language_code(item.language) or infer_language_from_result(result)
        data.append({
            "id": item.id,
            "recordId": item.id,
            "project_id": item.project_id,
            "contentPlanId": item.content_plan_id,
            "language": language_code,
            "target_language": language_code,
            "title": item.title,
            "script": item.original_script,
            "directions": json.loads(item.directions_json),
            "result": result,
            "createdAt": item.created_at.isoformat(),
        })
    return {"code": 0, "message": "success", "data": data}
