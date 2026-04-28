import json
import logging
import re
from typing import Any

from app.models.content_plan import ContentPlan
from app.models.short_drama_project import ShortDramaProject
from app.services.ai_service import request_ai_text


logger = logging.getLogger(__name__)

OUTLINE_SYSTEM_PROMPT = (
    "你是一个短剧分集大纲策划专家，擅长把项目级内容策划拆解成强冲突、强钩子、快节奏的多集短剧大纲。"
    "分集大纲是给编剧、运营、导演审核的内部生产稿，必须统一使用中文。"
    "你必须严格输出 JSON 对象，不要输出 Markdown，不要解释，不要输出代码块。"
)

OUTLINE_LANGUAGE_RULES = """
【分集大纲语言规则】
1. 你必须使用中文输出分集大纲。
2. 每一集的 title 必须是中文。
3. 每一集的 title 必须建议使用格式：第 X 集：中文标题。
4. 每一集的 summary 必须是中文。
5. 不允许 title 使用英文标题。
6. 不允许 summary 出现英文完整句子。
7. 即使项目目标市场是北美、东南亚，分集大纲也必须中文。
8. 目标市场只用于参考剧情风格、爽点偏好和投放节奏。
9. 海外语言版本会在后续本地化阶段生成。
10. 不要输出 Markdown。
11. 严格输出 JSON。
"""


def parse_content_plan_result(content_plan: ContentPlan | None) -> dict[str, Any]:
    if not content_plan:
        return {}
    try:
        result = json.loads(content_plan.result_json)
        return result if isinstance(result, dict) else {"raw": result}
    except Exception:
        return {}


def read_plan_text(result: dict[str, Any], keys: list[str]) -> str:
    for key in keys:
        value = result.get(key)
        if isinstance(value, list):
            text = "；".join(str(item) for item in value if item)
        elif value is None:
            text = ""
        else:
            text = str(value)
        if text.strip():
            return text.strip()
    return ""


def build_outline_context(project: ShortDramaProject, content_plan: ContentPlan | None) -> dict[str, str]:
    result = parse_content_plan_result(content_plan)
    return {
        "project_name": project.name,
        "genre": content_plan.genre if content_plan else (project.genre or "短剧"),
        "market": content_plan.market if content_plan else (project.target_market or "目标市场"),
        "language": content_plan.language if content_plan else (getattr(project, "primary_language", None) or project.language or "zh-CN"),
        "episode_count": str(project.episode_count or ""),
        "description": content_plan.selling_point if content_plan else (project.description or "围绕主角困境、反击和阶段性胜利推进剧情。"),
        "positioning": read_plan_text(result, ["positioning", "storyPositioning", "故事定位"]),
        "audience": read_plan_text(result, ["targetAudience", "目标用户"]),
        "conflict": read_plan_text(result, ["coreConflict", "核心冲突"]) or "主角被误解和压制后，逐步掌握证据并完成反击。",
        "hook": read_plan_text(result, ["openingHook", "threeSecondHook", "3秒开头建议", "前三秒开场建议"]) or "开场直接抛出背叛、危机或身份反转。",
        "highlights": read_plan_text(result, ["highlights", "sellingPoints", "爽点", "泪点", "反转点"]) or "身份反转、证据反击、情绪释放和追更悬念。",
        "suggestions": read_plan_text(result, ["suggestions", "aiSuggestions", "AI策划建议"]),
    }


def build_outline_user_prompt(
    project: ShortDramaProject,
    content_plan: ContentPlan | None,
    episode_count: int,
    start_episode_no: int,
    strict_language_retry: bool = False,
) -> str:
    context = build_outline_context(project, content_plan)
    plan_result = parse_content_plan_result(content_plan)
    plan_result_text = json.dumps(plan_result, ensure_ascii=False)[:6000] if plan_result else "无内容策划结构化结果，使用项目简介兜底。"

    retry_rule = "这是一次语言校验失败后的重试。请逐集检查 title 和 summary，禁止英文标题，禁止英文完整句子。" if strict_language_retry else ""

    return f"""
请基于以下短剧项目信息和内容策划结果，生成分集大纲。

项目信息：
- 项目名称：{project.name}
- 题材：{project.genre}
- 目标市场：{project.target_market}
- 主语言：{getattr(project, "primary_language", None) or project.language}
- 计划集数：{project.episode_count}
- 项目简介：{project.description or ""}

内容策划输入：
- 内容策划ID：{content_plan.id if content_plan else "无"}
- 策划项目名：{content_plan.project_name if content_plan else context["project_name"]}
- 策划题材：{content_plan.genre if content_plan else context["genre"]}
- 策划市场：{content_plan.market if content_plan else context["market"]}
- 策划语言：{content_plan.language if content_plan else context["language"]}
- 核心卖点：{content_plan.selling_point if content_plan else context["description"]}

内容策划结果 JSON：
{plan_result_text}

生成参数：
- episode_count：{episode_count}
- start_episode_no：{start_episode_no}

{OUTLINE_LANGUAGE_RULES}
{retry_rule}

输出要求：
1. 只输出 JSON，不要 Markdown，不要解释文字。
2. episodes 数量必须等于 {episode_count}。
3. episode_no 必须从 {start_episode_no} 开始连续递增。
4. title 要体现短剧爽点，不要空泛，必须为中文标题。
5. summary 必须包含四段：本集剧情推进、核心冲突、开场钩子、结尾悬念，且必须全中文。
6. 风格必须符合短剧：强冲突、强钩子、快节奏、每集结尾有悬念。

严格按以下格式输出：
{{
  "episodes": [
    {{
      "episode_no": {start_episode_no},
      "title": "第 {start_episode_no} 集：女主重生醒来",
      "summary": "本集剧情推进：...\\n核心冲突：...\\n开场钩子：...\\n结尾悬念：..."
    }}
  ]
}}
"""


def extract_json_text(text: str) -> str:
    content = text.strip()
    fence_match = re.search(r"```(?:json)?\s*(.*?)\s*```", content, flags=re.DOTALL | re.IGNORECASE)
    if fence_match:
        content = fence_match.group(1).strip()
    if content.startswith("{") and content.endswith("}"):
        return content
    start = content.find("{")
    end = content.rfind("}")
    if start >= 0 and end > start:
        return content[start : end + 1]
    return content


def count_pattern(pattern: str, text: str) -> int:
    return len(re.findall(pattern, text))


def contains_chinese(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text or ""))


def is_valid_chinese_episode_title(title: str) -> bool:
    text = (title or "").strip()
    if not contains_chinese(text):
        return False
    chinese_count = count_pattern(r"[\u4e00-\u9fff]", text)
    english_words = count_pattern(r"\b[A-Za-z]{2,}\b", text)
    return chinese_count >= max(1, english_words)


def is_valid_chinese_episode_summary(summary: str) -> bool:
    text = (summary or "").strip()
    chinese_count = count_pattern(r"[\u4e00-\u9fff]", text)
    english_words = count_pattern(r"\b[A-Za-z]{3,}\b", text)
    if chinese_count < 20:
        return False
    return chinese_count >= english_words * 2


def validate_episode_outline_language(episodes: list[dict[str, Any]]) -> bool:
    for item in episodes:
        if not is_valid_chinese_episode_title(str(item.get("title") or "")):
            return False
        if not is_valid_chinese_episode_summary(str(item.get("summary") or "")):
            return False
    return True


def parse_llm_outline_response(text: str, episode_count: int, start_episode_no: int) -> list[dict[str, Any]]:
    try:
        payload = json.loads(extract_json_text(text))
    except json.JSONDecodeError as exc:
        raise ValueError(f"JSON parse failed: {exc}") from exc

    episodes = payload.get("episodes") if isinstance(payload, dict) else None
    if not isinstance(episodes, list):
        raise ValueError("episodes must be a list")

    if len(episodes) < episode_count:
        raise ValueError(f"episodes count mismatch: expected {episode_count}, got {len(episodes)}")

    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(episodes[:episode_count]):
        if not isinstance(item, dict):
            raise ValueError(f"episode item {index} is not an object")
        title = str(item.get("title") or "").strip()
        summary = str(item.get("summary") or "").strip()
        if not title or not summary:
            raise ValueError(f"episode item {index} missing title or summary")
        normalized.append(
            {
                "episode_no": start_episode_no + index,
                "title": title,
                "summary": summary,
            }
        )
    if not validate_episode_outline_language(normalized):
        raise ValueError("分集大纲语言校验失败，title 或 summary 非中文")
    return normalized


def episode_phase(index: int, total: int) -> str:
    if index == 1:
        return "strong_opening"
    if index <= min(3, total):
        return "misunderstanding"
    if index >= max(total - 2, 1):
        return "reveal"
    return "escalation"


def title_for_phase(episode_no: int, phase: str, context: dict[str, str]) -> str:
    title_map = {
        "strong_opening": f"第 {episode_no} 集：危机开场，主角被迫反击",
        "misunderstanding": f"第 {episode_no} 集：误会加深，背叛浮出水面",
        "escalation": f"第 {episode_no} 集：冲突升级，反击计划推进",
        "reveal": f"第 {episode_no} 集：真相揭露，危机再升级",
    }
    return title_map.get(phase, f"第 {episode_no} 集：{context['project_name']}剧情推进")


def summary_for_phase(episode_no: int, phase: str, context: dict[str, str]) -> str:
    base_conflict = context["conflict"]
    hook = context["hook"]
    highlights = context["highlights"]
    if phase == "strong_opening":
        return (
            f"本集剧情推进：围绕《{context['project_name']}》的主冲突强开场，主角在关键场合遭遇压迫，被迫快速判断局势。\n"
            f"核心冲突：{base_conflict}\n"
            f"开场钩子：{hook}\n"
            "结尾悬念：主角发现眼前的背叛并不是偶然，背后还有更深的利益关系。"
        )
    if phase == "misunderstanding":
        return (
            f"本集剧情推进：第 {episode_no} 集继续放大身份误会和关系背叛，主角开始收集证据并试探对手。\n"
            "核心冲突：对手试图利用舆论、亲密关系或商业资源继续压制主角。\n"
            "开场钩子：主角刚要解释，就被新的证据或证人当众打断。\n"
            "结尾悬念：主角拿到一条关键线索，但线索指向最信任的人。"
        )
    if phase == "reveal":
        return (
            "本集剧情推进：剧情进入后段，真相逐步揭开，主角用前面积累的证据推进复仇或阶段性胜利。\n"
            "核心冲突：主角必须在公开场合完成反击，同时面对更大的新危机。\n"
            "开场钩子：对手以为胜券在握，主角却拿出能改写局势的关键证据。\n"
            f"结尾悬念：阶段性胜利后，更大的幕后人物出现，{highlights}"
        )
    return (
        f"本集剧情推进：第 {episode_no} 集进入中段升级，主角围绕证据、关系和资源展开主动反击。\n"
        f"核心冲突：{base_conflict}\n"
        "开场钩子：主角的计划刚有进展，对手立刻设置新的阻碍。\n"
        "结尾悬念：反击看似成功，却引出新的情感拉扯或人物反转。"
    )


def generate_rule_outline_items(
    project: ShortDramaProject,
    content_plan: ContentPlan | None,
    episode_count: int,
    start_episode_no: int,
) -> list[dict[str, Any]]:
    # 分集大纲是 AI/规则生成的初稿，后续可在分集管理页逐集调整。
    safe_count = max(1, min(episode_count, 30))
    start_no = max(1, start_episode_no)
    context = build_outline_context(project, content_plan)
    return [
        {
            "episode_no": start_no + index,
            "title": title_for_phase(start_no + index, episode_phase(index + 1, safe_count), context),
            "summary": summary_for_phase(start_no + index, episode_phase(index + 1, safe_count), context),
        }
        for index in range(safe_count)
    ]


def generate_episode_outline_items(
    project: ShortDramaProject,
    content_plan: ContentPlan | None,
    episode_count: int,
    start_episode_no: int,
) -> tuple[list[dict[str, Any]], str]:
    safe_count = max(1, min(episode_count, 30))
    start_no = max(1, start_episode_no)
    fallback_items = generate_rule_outline_items(project, content_plan, safe_count, start_no)
    for attempt in range(2):
        prompt = build_outline_user_prompt(project, content_plan, safe_count, start_no, strict_language_retry=attempt > 0)
        content, error = request_ai_text(OUTLINE_SYSTEM_PROMPT, prompt, response_format_json=True)
        if error or not content:
            logger.warning("Episode outline DeepSeek fallback: %s", error)
            return fallback_items, "rule_fallback"

        try:
            return parse_llm_outline_response(content, safe_count, start_no), "deepseek"
        except ValueError as exc:
            if "语言校验失败" in str(exc):
                logger.warning(
                    "分集大纲语言校验失败，title 或 summary 非中文，%s。",
                    "准备重试" if attempt == 0 else "使用规则 fallback",
                )
            else:
                logger.warning("Episode outline DeepSeek response invalid, %s: %s", "retry" if attempt == 0 else "fallback to rule", exc)
            if attempt == 0:
                continue
            return fallback_items, "rule_fallback"

    return fallback_items, "rule_fallback"
