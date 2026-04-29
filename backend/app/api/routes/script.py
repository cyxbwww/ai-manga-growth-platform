import json
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.script_polish import ScriptPolish
from app.models.short_drama_episode import ShortDramaEpisode
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
    episode_id: Optional[int] = None
    episode_no: Optional[int] = None
    title: str
    script: str
    directions: list[str]
    contentPlanId: Optional[int] = None
    # language 保存和传递字典 value，例如 en-US；Prompt 中再临时转成中文语言名。
    language: Optional[str] = None
    target_language: Optional[str] = None


def build_target_mock_polish(payload: ScriptPolishRequest, language_code: str) -> tuple[str, list[str]]:
    # mock 模式也按目标语言输出，避免按钮切换后仍看到英文内容。
    if language_code == "ja-JP":
        return (
            f"{payload.title} - 日本語版ブラッシュアップ\n"
            "[0-3秒] 結婚式場で、株式譲渡書類が大スクリーンに映る。義妹が冷たく笑う。「自分の会社も守れないのに、彼と結婚できると思ったの？」\n"
            "[3-10秒] ヒロインは静かに指輪をテーブルへ置く。「思い出させてくれてありがとう。今日サインするのは結婚契約じゃない。」\n"
            "[10-20秒] 弁護士が入ってきて、彼女が今も支配株主だと告げる。会場は一瞬で静まり返る。\n"
            "【引き】彼女は振り返らずに言う。「次回、奪われたものを全部取り戻す。」",
            [
                "冒頭の一言は説明ではなく挑発として見せる。",
                "証拠、立場逆転、沈黙で短劇らしい爽快感を作る。",
                "海外向け表現は裏切り、契約、支配権、反撃を明確にする。",
            ],
        )
    if language_code == "ko-KR":
        return (
            f"{payload.title} - 한국어 현지화 각색\n"
            "[0-3초] 결혼식장 대형 스크린에 주식 양도 서류가 뜬다. 의붓동생이 비웃으며 말한다. “네 회사도 못 지키면서 그 사람과 결혼할 수 있을 것 같아?”\n"
            "[3-10초] 여주인공은 침착하게 반지를 테이블에 내려놓는다. “알려줘서 고마워. 오늘 내가 서명할 건 결혼 계약서가 아니야.”\n"
            "[10-20초] 변호사가 들어와 그녀가 여전히 지배 주주라고 밝힌다. 식장은 순식간에 조용해진다.\n"
            "[클리프행어] 그녀는 뒤돌아보지 않고 말한다. “다음 회, 빼앗긴 모든 걸 되찾을 거야.”",
            [
                "첫 대사는 설명보다 도발처럼 느껴지게 만든다.",
                "증거, 지위 반전, 침묵으로 짧은 호흡의 카타르시스를 만든다.",
                "해외 시청자도 이해하기 쉬운 배신, 계약, 지배권, 반격을 강조한다.",
            ],
        )
    if language_code == "zh-CN":
        return (
            f"《{payload.title}》中文投放版片段\n"
            "【0-3秒】婚礼大屏亮出股权转让文件，继妹当众嘲讽女主连公司都守不住。\n"
            "【3-10秒】女主把戒指放到桌上，冷静宣布今天要签的不是婚约。\n"
            "【10-20秒】律师入场确认她仍是控股人，全场瞬间安静。\n"
            "【结尾钩子】女主离开前说：下一集，我会拿回属于我的一切。",
            [
                "开场直接给出背叛证据，减少解释铺垫。",
                "用身份反转和沉默制造爽点。",
                "突出背叛、契约、控制权和反击四个投放关键词。",
            ],
        )
    return (
        f"{payload.title} - localized polished excerpt\n"
        "[0-3s] At the wedding, a share transfer document appears on the big screen. The stepsister says, 'You could not even keep your company. Why would he marry you?'\n"
        "[3-10s] The heroine stays calm, places the ring on the table, and says, 'Thanks for the reminder. The contract I sign today is not a marriage contract.'\n"
        "[10-20s] Her lawyer walks in and confirms she is still the controlling shareholder. The room goes silent.\n"
        "[Cliffhanger] She walks away: 'Next episode, I take back everything they stole.'",
        [
            "Make the first line feel like a challenge, not an explanation.",
            "Use proof, status reversal, and silence to create a stronger short-drama payoff.",
            "Keep the overseas copy direct: betrayal, contract, control, comeback.",
        ],
    )


def build_script_polish_result(payload: ScriptPolishRequest) -> dict:
    # mock 打磨逻辑：原字段保留中文，bilingual.target 预留给海外投放表达。
    language_code = script_language_code(payload)
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
    target_polished, target_tips = build_target_mock_polish(payload, language_code)
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
            "target": {"language": language_code, "polishedScript": target_polished, "optimizationTips": target_tips},
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


def is_legacy_english_target_text(text: str | None, language_code: str) -> bool:
    # 旧 mock 曾把所有目标语言都写成英文；非英文语言读历史时做展示兼容。
    if language_code == "en-US" or not text:
        return False
    if "localized polished excerpt" in text or "At the wedding" in text:
        return True
    letters = sum(1 for char in text if ("a" <= char.lower() <= "z"))
    non_space = sum(1 for char in text if not char.isspace())
    return non_space > 40 and letters / non_space > 0.65


def normalize_script_polish_result(result: dict, language_code: str, fallback_data: dict) -> dict:
    # 兼容旧历史和模型偶发缺字段：目标语言统一使用 code，目标分支缺内容时只补同语言 mock 字段。
    if not isinstance(result, dict):
        return fallback_data

    bilingual = result.setdefault("bilingual", {})
    if not isinstance(bilingual, dict):
        result["bilingual"] = {}
        bilingual = result["bilingual"]

    zh_fallback = fallback_data.get("bilingual", {}).get("zh", {})
    target_fallback = fallback_data.get("bilingual", {}).get("target", {})

    zh = bilingual.get("zh")
    if not isinstance(zh, dict):
        zh = {}
        bilingual["zh"] = zh
    zh.setdefault("polishedScript", result.get("polishedScript") or zh_fallback.get("polishedScript") or "")
    zh.setdefault("optimizationTips", result.get("optimizationTips") or zh_fallback.get("optimizationTips") or [])

    target = bilingual.get("target")
    if not isinstance(target, dict):
        target = {}
        bilingual["target"] = target
    target["language"] = language_code
    target.setdefault("polishedScript", target_fallback.get("polishedScript") or "")
    target.setdefault("optimizationTips", target_fallback.get("optimizationTips") or [])
    if is_legacy_english_target_text(target.get("polishedScript"), language_code):
        target["polishedScript"] = target_fallback.get("polishedScript") or target.get("polishedScript") or ""
        target["optimizationTips"] = target_fallback.get("optimizationTips") or target.get("optimizationTips") or []
    return result


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
目标语言 code：{language_code}

要求：
1. 诊断节奏、冲突、反转、情绪张力。
2. 强化前三秒钩子，优化海外表达。
3. localizedVersion 不能只是直译，要像海外短剧投放文案一样改写。
4. {BILINGUAL_REQUIREMENT}
5. bilingual.target.polishedScript 和 bilingual.target.optimizationTips 必须使用 {language_name}；除非目标语言是英文，否则不要输出英文。
6. bilingual.target.language 必须填写目标语言 code：{language_code}，不要填写中文展示名。
7. 只返回 JSON 对象，字段必须严格如下：
{{
  "score": 0,
  "diagnostics": [{{"type": "string", "problem": "string", "suggestion": "string"}}],
  "polishedScript": "string",
  "localizedRewrite": [{{"original": "string", "directTranslation": "string", "localizedVersion": "string"}}],
  "optimizationTips": ["string"],
  "bilingual": {{
    "zh": {{"polishedScript": "string", "optimizationTips": ["string"]}},
    "target": {{"language": "{language_code}", "polishedScript": "string", "optimizationTips": ["string"]}}
  }}
}}
"""


def advance_episode_after_script_polish(db: Session, payload: ScriptPolishRequest) -> None:
    if not payload.episode_id:
        return
    try:
        query = db.query(ShortDramaEpisode).filter(ShortDramaEpisode.id == payload.episode_id)
        if payload.project_id:
            query = query.filter(ShortDramaEpisode.project_id == payload.project_id)
        episode = query.first()
        if not episode:
            return
        # 分集级剧本打磨完成后，推动该集进入 AI 分镜阶段；弱关联失败不影响主记录保存。
        episode.script_status = "completed"
        episode.stage = "storyboard"
        episode.updated_at = datetime.now()
        db.commit()
    except Exception as exc:
        db.rollback()
        print(f"更新分集剧本状态失败: {exc}")


@router.post("/polish")
def polish_script(payload: ScriptPolishRequest, db: Session = Depends(get_db)):
    language_code = script_language_code(payload)
    fallback_data = build_script_polish_result(payload)
    result = generate_json(SYSTEM_PROMPT, build_user_prompt(payload), fallback_data)
    result = normalize_script_polish_result(result, language_code, fallback_data)

    record = ScriptPolish(
        project_id=payload.project_id,
        episode_id=payload.episode_id,
        episode_no=payload.episode_no,
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
    advance_episode_after_script_polish(db, payload)

    return {
        "code": 0,
        "message": "success",
        "data": {
            "recordId": record.id,
            "project_id": payload.project_id,
            "episode_id": payload.episode_id,
            "episode_no": payload.episode_no,
            "language": language_code,
            "target_language": language_code,
            **result,
        },
    }


@router.get("/polishes")
def get_script_polish_history(
    project_id: Optional[int] = Query(default=None),
    episode_id: Optional[int] = Query(default=None),
    episode_no: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(ScriptPolish)
    if project_id is not None:
        query = query.filter(ScriptPolish.project_id == project_id)
    if episode_id is not None:
        query = query.filter(ScriptPolish.episode_id == episode_id)
    if episode_no is not None:
        query = query.filter(ScriptPolish.episode_no == episode_no)
    records = query.order_by(ScriptPolish.created_at.desc()).limit(20).all()
    data = []
    for item in records:
        result = json.loads(item.result_json)
        language_code = normalize_language_code(item.language) or infer_language_from_result(result)
        fallback_payload = ScriptPolishRequest(
            project_id=item.project_id,
            episode_id=item.episode_id,
            episode_no=item.episode_no,
            title=item.title,
            script=item.original_script,
            directions=json.loads(item.directions_json),
            contentPlanId=item.content_plan_id,
            language=language_code,
        )
        result = normalize_script_polish_result(result, language_code, build_script_polish_result(fallback_payload))
        data.append({
            "id": item.id,
            "recordId": item.id,
            "project_id": item.project_id,
            "episode_id": item.episode_id,
            "episode_no": item.episode_no,
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
