import json
import logging
import re
import time
from difflib import SequenceMatcher
from datetime import datetime
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from openai import OpenAI
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.config import (
    AI_API_KEY,
    AI_BASE_URL,
    AI_MODEL,
    AI_PROVIDER,
    AI_TEMPERATURE,
    AI_TIMEOUT,
    DEBUG_LLM_RESPONSE,
    ENABLE_STORYBOARD_MOCK_FALLBACK,
    STORYBOARD_LLM_MAX_TOKENS,
)
from app.core.database import get_db
from app.models.short_drama_episode import ShortDramaEpisode
from app.models.storyboard import Storyboard
from app.services.ai_service import request_ai_text
from app.services.project_flow import advance_project_stage


router = APIRouter(prefix="/storyboard")
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "你是一个 AI短剧内容生产助手，擅长把短剧剧本拆解为可生产的分镜数据。"
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

UNIQUENESS_MAIN_FIELDS = ["characterAction", "dialogue", "emotion", "visualPrompt", "motionPrompt"]
UNIQUENESS_ALL_FIELDS = [
    "scene",
    "characterAction",
    "dialogue",
    "emotion",
    "visualPrompt",
    "motionPrompt",
    "consistencyPrompt",
]
UNIQUENESS_FIELD_LABELS = {
    "scene": "scene",
    "characterAction": "action",
    "dialogue": "dialogue",
    "emotion": "emotion",
    "visualPrompt": "visualPrompt",
    "motionPrompt": "motionPrompt",
    "consistencyPrompt": "consistencyPrompt",
}
STORYBOARD_DUPLICATE_ERROR_CODE = "STORYBOARD_DUPLICATE_CONTENT"
STORYBOARD_JSON_PARSE_ERROR_CODE = "STORYBOARD_LLM_JSON_PARSE_FAILED"
STORYBOARD_GENERATION_ERROR_CODE = "STORYBOARD_LLM_GENERATION_FAILED"
RETRY_DUPLICATE_INSTRUCTION_LEGACY_LONG = """

【重复修复要求】
上一次生成结果多个分镜内容过度相似。
请重新生成，并严格保证：
- 每个分镜承担不同剧情功能。
- 不要复用同一句 scene。
- 不要复用同一句 action。
- 不要复用同一句 visualPrompt。
- 不要复用同一句 motionPrompt。
- 不要只改变分镜编号和时长。
- 第1镜用于建立场景。
- 第2镜用于制造冲突。
- 第3镜用于角色情绪变化。
- 第4镜用于关键动作或反击。
- 第5镜用于局势反转。
- 第6镜用于结尾悬念。
如果分镜数量不是6，也要按“开场、冲突、情绪、动作、反转、悬念”的节奏拆分。
"""


RETRY_DUPLICATE_INSTRUCTION_LEGACY_SHORT = """

【重试要求】
上次分镜 action/visualPrompt/motionPrompt 重复。请重新输出严格 JSON。
要求：
1. 保持 scenes 数量不变。
2. 每镜 action 不同。
3. 每镜 visualPrompt 不同，少于 40 个中文字或 80 个英文词。
4. 每镜 motionPrompt 不同，少于 30 个中文字或 60 个英文词。
5. 不要解释，不要 Markdown，只输出 JSON。

JSON 格式：
{
  "scenes": [
    {
      "sceneNo": 1,
      "scene": "同一场景也可以，但写清镜头位置",
      "action": "具体动作",
      "dialogue": "一句台词",
      "emotion": "情绪",
      "duration": 4,
      "visualPrompt": "短图片提示词",
      "motionPrompt": "短视频提示词",
      "consistencyPrompt": "短一致性提示词"
    }
  ]
}
"""


STORYBOARD_JSON_STABILITY_RULES = """
JSON 稳定性要求：
1. 只输出 JSON，不要 Markdown，不要解释文字，不要使用 ```json 包裹。
2. 不要在字符串中使用未转义的换行，所有字符串必须闭合。
3. 不要输出超长段落，不要在 JSON 后追加额外说明。
4. scenes 数量必须等于用户选择的分镜数量，sceneNo 从 1 开始递增。
5. duration 必须是数字，单位秒，范围 3 到 6。
"""


STORYBOARD_FIELD_LENGTH_RULES = """
字段长度和内容要求：
1. scene：不超过 40 个中文字符，用于描述镜头场景，例如“婚礼大厅证据对峙”。
2. action：不超过 120 个中文字符，用于描述本镜头核心动作；必须和其它镜头不同，不要只写“女主反击”这类过短模板。
3. dialogue：一句台词，不超过 80 个中文字符；没有台词时可为空字符串，不要每个镜头都重复同一句台词。
4. emotion：不超过 40 个中文字符，例如“压迫转反击”“震惊转冷静”“愤怒转失控”。
5. visualPrompt：不超过 180 个中文字符，必须包含画面主体、场景、人物动作、情绪、构图或光影；每个分镜必须不同，不要只写短关键词。
6. motionPrompt：不超过 150 个中文字符，描述镜头运动、人物动作变化、节奏变化；每个分镜必须不同，不要所有分镜都使用相同运镜。
7. consistencyPrompt：不超过 120 个中文字符，描述角色外观、服装、场景连续性；可以保留部分一致性信息，但不要每一镜完全一样。
"""


STORYBOARD_RHYTHM_RULES = """
内容差异化要求：
1. 每个分镜承担不同剧情功能，不要只改变 sceneNo 或 duration。
2. visualPrompt / motionPrompt 必须体现不同镜头。
3. 按短剧节奏拆分：开场建立场景、冲突压迫、角色情绪变化、关键动作或反击、局势反转、结尾悬念。
4. 如果分镜数量不是 6，也按“开场、冲突、情绪、动作、反转、悬念”的节奏自适应拆分。
5. 允许同一 scene 连续多镜，例如婚礼现场连续多镜，但 action / visualPrompt / motionPrompt 必须不同。
"""


RETRY_DUPLICATE_INSTRUCTION = f"""
【重试要求】
上次分镜 visualPrompt 或 motionPrompt 重复。请重新输出严格 JSON，并保持 scenes 数量不变。

{STORYBOARD_JSON_STABILITY_RULES}
{STORYBOARD_FIELD_LENGTH_RULES}
{STORYBOARD_RHYTHM_RULES}

JSON 格式：
{{
  "scenes": [
    {{
      "sceneNo": 1,
      "scene": "婚礼大厅证据对峙",
      "action": "女主从沉默中抬眼，将证据推到众人面前，迫使反派停止逼问",
      "dialogue": "证据就在这里，你还要继续装吗？",
      "emotion": "压迫转反击",
      "duration": 4,
      "visualPrompt": "婚礼大厅中女主站在长桌前推开证据文件，宾客围观，反派表情僵住，冷白灯光形成强对峙构图",
      "motionPrompt": "镜头从反派逼近的手势切到女主抬眼，再缓慢推近证据文件，节奏由压迫转为反击",
      "consistencyPrompt": "女主白色礼服和冷静眼神保持一致，婚礼大厅布景连续"
    }}
  ]
}}
"""


class StoryboardGenerateRequest(BaseModel):
    project_id: Optional[int] = None
    episode_id: Optional[int] = None
    episode_no: Optional[int] = None
    title: str
    script: str
    style: str
    sceneCount: int
    contentPlanId: Optional[int] = None
    scriptPolishId: Optional[int] = None


def text_or_empty(value: Any) -> str:
    return value if isinstance(value, str) else ""


def truncate_for_llm_debug(value: Any, limit: int = 200) -> str:
    text = text_or_empty(value).replace("\n", " ").replace("\r", " ").strip()
    return text[:limit]


def log_storyboard_raw_response(raw_text: str) -> None:
    if not DEBUG_LLM_RESPONSE:
        return
    logger.info(
        "[LLM_DEBUG][storyboard][raw_response] model=%s max_tokens=%s content=%s",
        AI_MODEL,
        STORYBOARD_LLM_MAX_TOKENS,
        raw_text[:3000],
    )
    logger.info(
        "[LLM_DEBUG][storyboard][raw_response_tail] model=%s tail=%s",
        AI_MODEL,
        raw_text[-500:],
    )


def log_storyboard_parsed_result(parsed: Any) -> None:
    if not DEBUG_LLM_RESPONSE:
        return
    scenes = parsed.get("scenes") if isinstance(parsed, dict) else []
    if not isinstance(scenes, list):
        scenes = []
    logger.info("[LLM_DEBUG][storyboard][parsed_summary] model=%s scene_count=%s", AI_MODEL, len(scenes))
    for index, scene in enumerate(scenes, start=1):
        scene_data = scene if isinstance(scene, dict) else {}
        logger.info(
            "[LLM_DEBUG][storyboard][parsed_scene] index=%s title=%s scene=%s action=%s visualPrompt=%s motionPrompt=%s",
            index,
            truncate_for_llm_debug(scene_data.get("title")),
            truncate_for_llm_debug(scene_data.get("scene")),
            truncate_for_llm_debug(scene_data.get("characterAction") or scene_data.get("action")),
            truncate_for_llm_debug(scene_data.get("visualPrompt")),
            truncate_for_llm_debug(scene_data.get("motionPrompt")),
        )


def log_storyboard_parse_error(exc: json.JSONDecodeError) -> None:
    if not DEBUG_LLM_RESPONSE:
        return
    logger.info(
        "[LLM_DEBUG][storyboard][parse_error] model=%s reason=%s line=%s column=%s position=%s",
        AI_MODEL,
        exc.msg,
        exc.lineno,
        exc.colno,
        exc.pos,
    )


def log_storyboard_normalized_result(result: dict) -> None:
    if not DEBUG_LLM_RESPONSE:
        return
    scenes = result.get("scenes") if isinstance(result, dict) else []
    if not isinstance(scenes, list):
        scenes = []
    logger.info("[LLM_DEBUG][storyboard][normalized_summary] model=%s scene_count=%s", AI_MODEL, len(scenes))
    for index, scene in enumerate(scenes, start=1):
        scene_data = scene if isinstance(scene, dict) else {}
        logger.info(
            "[LLM_DEBUG][storyboard][normalized_scene] index=%s scene=%s action=%s visualPrompt=%s motionPrompt=%s",
            index,
            truncate_for_llm_debug(scene_data.get("scene")),
            truncate_for_llm_debug(scene_data.get("characterAction") or scene_data.get("action")),
            truncate_for_llm_debug(scene_data.get("visualPrompt")),
            truncate_for_llm_debug(scene_data.get("motionPrompt")),
        )


def generate_storyboard_json(user_prompt: str, fallback_data: dict) -> dict:
    # 分镜专用 DeepSeek 调用包装：DeepSeek 未启用时保留 mock 演示；已返回 raw_text 但 JSON 失败时直接暴露错误。
    logger.info("Storyboard DeepSeek request max_tokens=%s", STORYBOARD_LLM_MAX_TOKENS)
    content, error = request_ai_text(SYSTEM_PROMPT, user_prompt, response_format_json=True, max_tokens=STORYBOARD_LLM_MAX_TOKENS)
    if error or not content:
        if AI_PROVIDER != "deepseek" or not AI_API_KEY or ENABLE_STORYBOARD_MOCK_FALLBACK:
            logger.warning("DeepSeek unavailable, using mock fallback: %s", error)
            return fallback_data
        logger.warning("DeepSeek storyboard generation failed without mock fallback: %s", error)
        raise_storyboard_generation_error(error or "DeepSeek returned empty content")

    log_storyboard_raw_response(content)
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        log_storyboard_parse_error(exc)
        logger.warning("DeepSeek storyboard JSON parse failed: %s", exc)
        raise_storyboard_parse_error(exc, content)
    log_storyboard_parsed_result(parsed)
    return parsed


def normalize_prompt_text_legacy(text: str) -> str:
    # 分镜重复检测只做轻量归一化：去掉编号、时长和常见模板词，避免 AI 只改序号就通过校验。
    text = text_or_empty(text).lower()
    text = re.sub(r"(scene|shot|镜头|分镜|第)\s*\d+\s*(镜|幕|场|号)?", " ", text)
    text = re.sub(r"\d+\s*(秒|s|sec|seconds|分钟|min|minutes)", " ", text)
    text = re.sub(r"\d+", " ", text)
    text = re.sub(r"[，。！？、；：,.!?;:()\[\]{}<>《》\"'“”‘’|/\\_-]+", " ", text)
    stop_words = {
        "the",
        "a",
        "an",
        "and",
        "or",
        "to",
        "of",
        "in",
        "on",
        "with",
        "for",
        "from",
        "then",
        "this",
        "that",
        "ai",
        "image",
        "video",
        "generation",
        "scene",
        "shot",
        "camera",
        "prompt",
        "分镜",
        "镜头",
        "场景",
        "画面",
        "提示词",
        "生成",
        "适合",
        "用于",
        "一个",
        "多个",
        "时长",
    }
    tokens = [token for token in text.split() if token and token not in stop_words]
    return " ".join(tokens)


def similarity_score(a: str, b: str) -> float:
    normalized_a = normalize_prompt_text(a)
    normalized_b = normalize_prompt_text(b)
    if not normalized_a or not normalized_b:
        return 0
    tokens_a = set(normalized_a.split())
    tokens_b = set(normalized_b.split())
    jaccard = len(tokens_a & tokens_b) / len(tokens_a | tokens_b) if tokens_a and tokens_b else 0
    sequence = SequenceMatcher(None, normalized_a, normalized_b).ratio()
    return max(jaccard, sequence)


def is_short_generic_text(text: str) -> bool:
    normalized = normalize_prompt_text(text)
    if not normalized:
        return True
    compact = normalized.replace(" ", "")
    generic_words = {"压迫", "反击", "待生成", "冲突", "转场", "悬念", "情绪", "动作", "comeback", "conflict", "pending"}
    return len(compact) <= 6 or compact in generic_words


def scene_text_value(scene: dict, field: str) -> str:
    value = scene.get(field)
    if field == "characterAction" and not value:
        value = scene.get("action")
    return text_or_empty(value)


def field_duplicate_ratio(values: list[str]) -> float:
    if len(values) < 2:
        return 0
    duplicate_indexes: set[int] = set()
    normalized_values = [normalize_prompt_text(value) for value in values]
    for left in range(len(values)):
        for right in range(left + 1, len(values)):
            if not normalized_values[left] or not normalized_values[right]:
                continue
            if normalized_values[left] == normalized_values[right] or similarity_score(values[left], values[right]) >= 0.85:
                duplicate_indexes.add(left)
                duplicate_indexes.add(right)
    return len(duplicate_indexes) / len(values)


def validate_storyboard_uniqueness_legacy(scenes: list) -> tuple[bool, list[str]]:
    # 在入库前拦截高度模板化的 AI 输出；这里只判定失败，不做规则兜底或字段替换。
    if not isinstance(scenes, list) or not scenes:
        return False, ["分镜内容为空"]

    reasons: list[str] = []
    dict_scenes = [scene if isinstance(scene, dict) else {} for scene in scenes]

    for field in UNIQUENESS_MAIN_FIELDS:
        values = [scene_text_value(scene, field).strip() for scene in dict_scenes if scene_text_value(scene, field).strip()]
        normalized_values = [normalize_prompt_text(value) for value in values]
        if len(normalized_values) >= 2 and len(set(normalized_values)) < len(normalized_values):
            reasons.append(f"{UNIQUENESS_FIELD_LABELS[field]} 完全重复")

    scene_count = len(dict_scenes)
    if scene_count >= 4:
        ratio_fields = ["visualPrompt", "motionPrompt", "characterAction"]
        for field in ratio_fields:
            values = [scene_text_value(scene, field) for scene in dict_scenes]
            if field_duplicate_ratio(values) > 0.5:
                reasons.append(f"{UNIQUENESS_FIELD_LABELS[field]} 重复度过高")

    short_generic_count = 0
    for scene in dict_scenes:
        checked_values = [scene_text_value(scene, field) for field in UNIQUENESS_ALL_FIELDS]
        if sum(1 for value in checked_values if is_short_generic_text(value)) >= 4:
            short_generic_count += 1
    if short_generic_count >= max(2, scene_count // 2):
        reasons.append("分镜内容过于模板化")

    unique_reasons = list(dict.fromkeys(reasons))
    return len(unique_reasons) == 0, unique_reasons


def exact_duplicate_ratio(values: list[str]) -> float:
    normalized_values = [normalize_prompt_text(value) for value in values]
    duplicate_indexes: set[int] = set()
    for left in range(len(normalized_values)):
        if not normalized_values[left]:
            continue
        for right in range(left + 1, len(normalized_values)):
            if normalized_values[left] == normalized_values[right]:
                duplicate_indexes.add(left)
                duplicate_indexes.add(right)
    return len(duplicate_indexes) / len(values) if values else 0


def has_repeated_nonempty_value(values: list[str]) -> bool:
    seen: set[str] = set()
    for value in values:
        normalized = normalize_prompt_text(value)
        if not normalized:
            continue
        if normalized in seen:
            return True
        seen.add(normalized)
    return False


def normalize_prompt_text(text: str) -> str:
    value = text_or_empty(text).lower()
    value = re.sub(r"(scene|shot)\s*\d+", " ", value)
    value = re.sub(r"(第\s*\d+\s*(镜|幕|场|段)|分镜\s*\d+|镜头\s*\d+)", " ", value)
    value = re.sub(r"\d+\s*(秒|s|sec|seconds|分钟|min|minutes)", " ", value)
    value = re.sub(r"\d+", " ", value)
    value = re.sub(r"[，。！？、；：,.!?;:()\[\]{}<>《》“”‘’\"'/\\_-]+", " ", value)
    value = re.sub(r"\s+", " ", value).strip()
    stop_words = {
        "the",
        "a",
        "an",
        "and",
        "or",
        "to",
        "of",
        "in",
        "on",
        "with",
        "for",
        "from",
        "then",
        "this",
        "that",
        "ai",
        "image",
        "video",
        "generation",
        "scene",
        "shot",
        "camera",
        "prompt",
        "分镜",
        "镜头",
        "场景",
        "画面",
        "提示词",
        "生成",
        "适合",
        "用于",
    }
    tokens = [token for token in value.split() if token and token not in stop_words]
    return " ".join(tokens)


def validate_storyboard_uniqueness_legacy_v2(scenes: list) -> dict:
    # 分镜去重只拦截强重复；同一 scene 连续多镜是短剧常见拍法，仅记录 warning。
    if not isinstance(scenes, list) or not scenes:
        return {"passed": False, "reasons": ["分镜内容为空"], "warnings": []}

    reasons: list[str] = []
    warnings: list[str] = []
    dict_scenes = [scene if isinstance(scene, dict) else {} for scene in scenes]
    scene_count = len(dict_scenes)

    scene_values = [scene_text_value(scene, "scene") for scene in dict_scenes]
    if has_repeated_nonempty_value(scene_values):
        warnings.append("scene 多镜重复，但允许同场景连续拍摄")

    if scene_count >= 4:
        action_values = [scene_text_value(scene, "characterAction") for scene in dict_scenes]
        if exact_duplicate_ratio(action_values) > 0.5:
            reasons.append("action 重复度过高")

        visual_values = [scene_text_value(scene, "visualPrompt") for scene in dict_scenes]
        if field_duplicate_ratio(visual_values) > 0.5:
            reasons.append("visualPrompt 重复度过高")

        motion_values = [scene_text_value(scene, "motionPrompt") for scene in dict_scenes]
        if field_duplicate_ratio(motion_values) > 0.5:
            reasons.append("motionPrompt 重复度过高")

    dialogue_values = [scene_text_value(scene, "dialogue") for scene in dict_scenes]
    if has_repeated_nonempty_value(dialogue_values):
        reasons.append("dialogue 重复度过高")

    emotion_values = [scene_text_value(scene, "emotion") for scene in dict_scenes]
    if (
        scene_count >= 4
        and exact_duplicate_ratio(emotion_values) > 0.5
        and exact_duplicate_ratio([scene_text_value(scene, "characterAction") for scene in dict_scenes]) > 0.5
        and field_duplicate_ratio([scene_text_value(scene, "visualPrompt") for scene in dict_scenes]) > 0.5
        and field_duplicate_ratio([scene_text_value(scene, "motionPrompt") for scene in dict_scenes]) > 0.5
    ):
        reasons.append("分镜内容过于模板化")

    short_generic_count = 0
    for scene in dict_scenes:
        checked_values = [scene_text_value(scene, field) for field in ["characterAction", "dialogue", "emotion", "visualPrompt", "motionPrompt"]]
        if sum(1 for value in checked_values if is_short_generic_text(value)) >= 3:
            short_generic_count += 1
    if short_generic_count >= max(2, scene_count // 2):
        reasons.append("分镜内容过于模板化")

    unique_reasons = list(dict.fromkeys(reasons))
    unique_warnings = list(dict.fromkeys(warnings))
    return {"passed": len(unique_reasons) == 0, "reasons": unique_reasons, "warnings": unique_warnings}


def validate_storyboard_uniqueness(scenes: list) -> dict:
    # 分镜去重只拦截画面/运镜提示词的强重复；同场景、同动作主题、同一句台词可以拆成多镜。
    if not isinstance(scenes, list) or not scenes:
        return {"passed": False, "reasons": ["分镜内容为空"], "warnings": []}

    reasons: list[str] = []
    warnings: list[str] = []
    dict_scenes = [scene if isinstance(scene, dict) else {} for scene in scenes]
    scene_count = len(dict_scenes)

    scene_values = [scene_text_value(scene, "scene") for scene in dict_scenes]
    if has_repeated_nonempty_value(scene_values):
        warnings.append("scene 多镜重复，但允许同场景连续拍摄")

    action_duplicate_ratio = 0.0
    visual_duplicate_ratio = 0.0
    motion_duplicate_ratio = 0.0

    if scene_count >= 4:
        action_values = [scene_text_value(scene, "characterAction") for scene in dict_scenes]
        action_duplicate_ratio = exact_duplicate_ratio(action_values)
        if action_duplicate_ratio > 0.5:
            warnings.append("action 重复度较高，已降级为提示，是否重试以 visualPrompt/motionPrompt 为准")

        visual_values = [scene_text_value(scene, "visualPrompt") for scene in dict_scenes]
        visual_duplicate_ratio = field_duplicate_ratio(visual_values)
        if visual_duplicate_ratio > 0.5:
            reasons.append("visualPrompt 重复度过高")

        motion_values = [scene_text_value(scene, "motionPrompt") for scene in dict_scenes]
        motion_duplicate_ratio = field_duplicate_ratio(motion_values)
        if motion_duplicate_ratio > 0.5:
            reasons.append("motionPrompt 重复度过高")

    dialogue_values = [scene_text_value(scene, "dialogue") for scene in dict_scenes]
    if has_repeated_nonempty_value(dialogue_values):
        warnings.append("dialogue 重复度较高，允许同一句关键台词拆多镜")

    emotion_values = [scene_text_value(scene, "emotion") for scene in dict_scenes]
    if (
        scene_count >= 4
        and exact_duplicate_ratio(emotion_values) > 0.5
        and action_duplicate_ratio > 0.5
        and visual_duplicate_ratio > 0.5
        and motion_duplicate_ratio > 0.5
    ):
        reasons.append("分镜内容过于模板化")

    short_generic_count = 0
    for scene in dict_scenes:
        checked_values = [
            scene_text_value(scene, field)
            for field in ["characterAction", "dialogue", "emotion", "visualPrompt", "motionPrompt"]
        ]
        if sum(1 for value in checked_values if is_short_generic_text(value)) >= 3:
            short_generic_count += 1
    if (
        short_generic_count >= max(2, scene_count // 2)
        and visual_duplicate_ratio > 0.5
        and motion_duplicate_ratio > 0.5
    ):
        reasons.append("分镜内容过于模板化")

    unique_reasons = list(dict.fromkeys(reasons))
    unique_warnings = list(dict.fromkeys(warnings))
    return {"passed": len(unique_reasons) == 0, "reasons": unique_reasons, "warnings": unique_warnings}


def build_duplicate_retry_prompt(payload: "StoryboardGenerateRequest") -> str:
    # 重试阶段只保留必要上下文和短 JSON 约束，降低模型输出过长导致 JSON 截断的概率。
    script_preview = payload.script[:1200]
    return f"""
请根据以下短剧剧本重新生成 AI 分镜 JSON。

标题：{payload.title}
剧本：{script_preview}
风格：{payload.style}
分镜数量：{payload.sceneCount}

{RETRY_DUPLICATE_INSTRUCTION}
"""


def raise_duplicate_storyboard_error(reasons: list[str]) -> None:
    raise HTTPException(
        status_code=422,
        detail={
            "code": STORYBOARD_DUPLICATE_ERROR_CODE,
            "message": "AI分镜结果重复度过高，请调整剧本文本或降低分镜数量后重试。",
            "reasons": reasons,
        },
    )


def raise_storyboard_parse_error(exc: json.JSONDecodeError, raw_text: str) -> None:
    detail = {
        "code": STORYBOARD_JSON_PARSE_ERROR_CODE,
        "message": "AI分镜结果解析失败，请重试或调整剧本文本。",
        "reason": str(exc),
    }
    if DEBUG_LLM_RESPONSE:
        detail["raw_preview"] = raw_text[:1000]
    raise HTTPException(status_code=422, detail=detail)


def raise_storyboard_generation_error(reason: str) -> None:
    raise HTTPException(
        status_code=503,
        detail={
            "code": STORYBOARD_GENERATION_ERROR_CODE,
            "message": "AI分镜生成失败，请稍后重试或切换 mock 演示模式。",
            "reason": reason,
        },
    )


def build_scene(index: int, style: str, title: str) -> dict:
    # mock fallback 也必须返回完整 bilingual 对象，保证前端切换语言时不会出现空白。
    duration = "4秒" if index <= 2 else "5秒"
    zh = {
        "title": f"{title} 分镜 {index}",
        "scene": f"第{index}幕发生在高压对峙场景中，镜头聚焦主角与对手的情绪变化。",
        "characterAction": "主角从被动沉默转为主动反击，抬眼、停顿、亮出关键证据。",
        "dialogue": "主角：今天结束的不是婚礼，是你们的谎言。",
        "emotion": ["压迫", "震惊", "反击", "反转", "释放", "悬念", "决断", "追更"][(index - 1) % 8],
        "visualPrompt": f"{style}，竖屏短剧分镜，第{index}幕，婚礼现场强冲突，主角冷静反击，电影级灯光，适合AI图片生成",
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


def build_user_prompt_legacy(payload: StoryboardGenerateRequest) -> str:
    return f"""
请把以下剧本拆解成可生产的 AI短剧分镜。

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


def build_user_prompt_legacy_short(payload: StoryboardGenerateRequest) -> str:
    script_preview = payload.script[:1500]
    return f"""
请基于以下剧本片段生成 AI短剧分镜草稿。

标题：{payload.title}
剧本片段：{script_preview}
画面风格：{payload.style}
分镜数量：{payload.sceneCount}

只输出合法 JSON，不要 Markdown，不要解释。所有字符串必须闭合，不要换行写超长字段。
每个分镜内容要不同，不能只改编号。

字段长度限制：
- scene：不超过 20 个中文字符
- action：不超过 35 个中文字符
- dialogue：一句话，不超过 30 个中文字符
- emotion：不超过 15 个中文字符
- visualPrompt：不超过 60 个中文字符
- motionPrompt：不超过 50 个中文字符
- consistencyPrompt：不超过 50 个中文字符

JSON 格式：
{{
  "storyboardTitle": "{payload.title}",
  "style": "{payload.style}",
  "scenes": [
    {{
      "sceneNo": 1,
      "scene": "短场景",
      "action": "具体动作",
      "dialogue": "一句台词",
      "emotion": "情绪",
      "duration": 4,
      "visualPrompt": "短图片提示词",
      "motionPrompt": "短视频提示词",
      "consistencyPrompt": "短一致性提示词"
    }}
  ]
}}
"""


def build_user_prompt(payload: StoryboardGenerateRequest) -> str:
    script_preview = payload.script[:1500]
    return f"""
请基于以下剧本片段生成 AI短剧分镜草稿。

标题：{payload.title}
剧本片段：{script_preview}
画面风格：{payload.style}
分镜数量：{payload.sceneCount}

{STORYBOARD_JSON_STABILITY_RULES}
{STORYBOARD_FIELD_LENGTH_RULES}
{STORYBOARD_RHYTHM_RULES}

JSON 格式：
{{
  "storyboardTitle": "{payload.title}",
  "style": "{payload.style}",
  "scenes": [
    {{
      "sceneNo": 1,
      "scene": "婚礼大厅证据对峙",
      "action": "女主从沉默中抬眼，将证据推到众人面前，迫使反派停止逼问",
      "dialogue": "证据就在这里，你还要继续装吗？",
      "emotion": "压迫转反击",
      "duration": 4,
      "visualPrompt": "婚礼大厅中女主站在长桌前推开证据文件，宾客围观，反派表情僵住，冷白灯光形成强对峙构图",
      "motionPrompt": "镜头从反派逼近的手势切到女主抬眼，再缓慢推近证据文件，节奏由压迫转为反击",
      "consistencyPrompt": "女主白色礼服和冷静眼神保持一致，婚礼大厅布景连续"
    }}
  ]
}}
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
        "characterAction": text_or_empty(source.get("characterAction")) or text_or_empty(source.get("action")) or text_or_empty(scene.get("characterAction")) or text_or_empty(scene.get("action")),
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

    # 优先使用 AI 原始 bilingual；如果 AI 只返回顶层字段，不能让 fallback bilingual 覆盖真实输出。
    raw_bilingual = scene.get("bilingual") if isinstance(scene.get("bilingual"), dict) else {}
    bilingual = raw_bilingual if raw_bilingual else {}
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
        project_id=payload.project_id,
        episode_id=payload.episode_id,
        episode_no=payload.episode_no,
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
    advance_project_stage(db, payload.project_id, "localization")
    # 分集级生产状态流转：分镜生成完成后，该集进入本地化准备阶段；失败不影响主流程返回。
    if payload.episode_id:
        try:
            episode = db.query(ShortDramaEpisode).filter(ShortDramaEpisode.id == payload.episode_id).first()
            if episode:
                episode.storyboard_status = "completed"
                episode.stage = "localization"
                episode.updated_at = datetime.now()
                db.commit()
        except Exception as exc:
            db.rollback()
            print(f"分镜生成后更新分集状态失败，已忽略：episode_id={payload.episode_id}, error={exc}")
    return record


def stream_deepseek_storyboard(payload: StoryboardGenerateRequest, fallback_data: dict) -> dict:
    logger.info("Storyboard DeepSeek stream request max_tokens=%s", STORYBOARD_LLM_MAX_TOKENS)
    client = OpenAI(api_key=AI_API_KEY, base_url=AI_BASE_URL, timeout=AI_TIMEOUT)
    response = client.chat.completions.create(
        model=AI_MODEL,
        messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": build_user_prompt(payload)}],
        temperature=AI_TEMPERATURE,
        max_tokens=STORYBOARD_LLM_MAX_TOKENS,
        response_format={"type": "json_object"},
        stream=True,
    )
    content = ""
    for chunk in response:
        delta = chunk.choices[0].delta.content
        if delta:
            content += delta
    log_storyboard_raw_response(content)
    try:
        parsed = json.loads(content)
    except json.JSONDecodeError as exc:
        log_storyboard_parse_error(exc)
        logger.warning("DeepSeek storyboard stream JSON parse failed: %s", exc)
        raise_storyboard_parse_error(exc, content)
    log_storyboard_parsed_result(parsed)
    return normalize_storyboard_result(parsed, fallback_data, payload.sceneCount)


@router.post("/generate")
def generate_storyboard(payload: StoryboardGenerateRequest, db: Session = Depends(get_db)):
    fallback_data = build_storyboard_result(payload)
    ai_result = generate_storyboard_json(build_user_prompt(payload), fallback_data)
    result = normalize_storyboard_result(ai_result, fallback_data, payload.sceneCount)
    log_storyboard_normalized_result(result)
    uniqueness = validate_storyboard_uniqueness(result["scenes"])
    logger.warning(
        "Storyboard uniqueness check attempt=1 passed=%s reasons=%s warnings=%s",
        uniqueness["passed"],
        uniqueness["reasons"],
        uniqueness["warnings"],
    )
    if not uniqueness["passed"]:
        reasons = uniqueness["reasons"]
        logger.warning("AI分镜结果重复度过高，准备重试。reasons=%s", reasons)
        retry_ai_result = generate_storyboard_json(build_duplicate_retry_prompt(payload), fallback_data)
        result = normalize_storyboard_result(retry_ai_result, fallback_data, payload.sceneCount)
        log_storyboard_normalized_result(result)
        retry_uniqueness = validate_storyboard_uniqueness(result["scenes"])
        retry_reasons = retry_uniqueness["reasons"]
        logger.warning(
            "Storyboard uniqueness check attempt=2 passed=%s reasons=%s warnings=%s",
            retry_uniqueness["passed"],
            retry_reasons,
            retry_uniqueness["warnings"],
        )
        if not retry_uniqueness["passed"]:
            logger.warning("Storyboard generation rejected by duplicate check. reasons=%s", retry_reasons)
            raise_duplicate_storyboard_error(retry_reasons)
    record = save_storyboard_record(payload, result, db)
    return {
        "code": 0,
        "message": "success",
        "data": {"recordId": record.id, "project_id": payload.project_id, "episode_id": payload.episode_id, "episode_no": payload.episode_no, **result},
    }


@router.post("/stream")
def stream_storyboard(payload: StoryboardGenerateRequest, db: Session = Depends(get_db)):
    fallback_data = build_storyboard_result(payload)

    def event_generator():
        yield sse_event({"type": "meta", "data": {"storyboardTitle": fallback_data["storyboardTitle"], "style": fallback_data["style"]}})
        result = fallback_data
        try:
            if AI_PROVIDER == "deepseek" and AI_API_KEY:
                result = stream_deepseek_storyboard(payload, fallback_data)
        except HTTPException as exc:
            yield sse_event({"type": "error", "data": exc.detail})
            return
        except Exception as exc:
            if AI_PROVIDER == "deepseek" and AI_API_KEY and not ENABLE_STORYBOARD_MOCK_FALLBACK:
                logger.warning("DeepSeek storyboard stream failed without mock fallback: %s", exc)
                yield sse_event(
                    {
                        "type": "error",
                        "data": {
                            "code": STORYBOARD_GENERATION_ERROR_CODE,
                            "message": "AI分镜生成失败，请稍后重试或切换 mock 演示模式。",
                            "reason": str(exc),
                        },
                    }
                )
                return
            logger.warning("DeepSeek storyboard stream failed, using mock fallback: %s", exc)
            result = fallback_data
        result = normalize_storyboard_result(result, fallback_data, payload.sceneCount)
        log_storyboard_normalized_result(result)
        for scene in result["scenes"]:
            yield sse_event({"type": "scene", "data": scene})
            time.sleep(0.3)
        record = save_storyboard_record(payload, result, db)
        yield sse_event({"type": "done", "data": {"recordId": record.id, "project_id": payload.project_id, "episode_id": payload.episode_id, "episode_no": payload.episode_no}})

    return StreamingResponse(event_generator(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


@router.get("/list")
def get_storyboard_history(
    project_id: Optional[int] = Query(default=None),
    episode_id: Optional[int] = Query(default=None),
    episode_no: Optional[int] = Query(default=None),
    db: Session = Depends(get_db),
):
    query = db.query(Storyboard)
    if project_id:
        query = query.filter(Storyboard.project_id == project_id)
    if episode_id:
        query = query.filter(Storyboard.episode_id == episode_id)
    if episode_no:
        query = query.filter(Storyboard.episode_no == episode_no)
    records = query.order_by(Storyboard.created_at.desc()).limit(20).all()
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
                "project_id": item.project_id,
                "episode_id": item.episode_id,
                "episode_no": item.episode_no,
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
