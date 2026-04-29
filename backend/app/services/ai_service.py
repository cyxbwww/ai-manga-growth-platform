import json
import logging

from openai import OpenAI

from app.core.config import (
    AI_API_KEY,
    AI_BASE_URL,
    AI_MAX_TOKENS,
    AI_MODEL,
    AI_PROVIDER,
    AI_TEMPERATURE,
    AI_TIMEOUT,
)


logger = logging.getLogger(__name__)


def request_ai_text(system_prompt: str, user_prompt: str, response_format_json: bool = True, max_tokens: int | None = None) -> tuple[str | None, str | None]:
    # 统一复用 DeepSeek/OpenAI 兼容调用封装；业务层根据 error 决定是否走 fallback。
    if AI_PROVIDER != "deepseek":
        return None, f"AI_PROVIDER={AI_PROVIDER}"

    if not AI_API_KEY:
        # 不打印或返回真实 Key，只记录缺少配置。
        return None, "AI_API_KEY is empty"

    try:
        # DeepSeek 兼容 OpenAI SDK，通过 base_url 指向 DeepSeek API。
        client = OpenAI(
            api_key=AI_API_KEY,
            base_url=AI_BASE_URL,
            timeout=AI_TIMEOUT,
        )
        response = client.chat.completions.create(
            model=AI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=AI_TEMPERATURE,
            max_tokens=max_tokens or AI_MAX_TOKENS,
            response_format={"type": "json_object"} if response_format_json else None,
        )
        content = response.choices[0].message.content
        if not content:
            return None, "DeepSeek returned empty content"
        return content, None
    except Exception as exc:
        return None, str(exc)


def generate_json(system_prompt: str, user_prompt: str, fallback_data: dict) -> dict:
    # mock 模式或 DeepSeek 异常时强制使用 fallback，保证面试演示和本地开发稳定可用。
    content, error = request_ai_text(system_prompt, user_prompt, response_format_json=True)
    if error or not content:
        logger.warning("DeepSeek unavailable, using mock fallback: %s", error)
        return fallback_data

    try:
        return json.loads(content)
    except json.JSONDecodeError as exc:
        logger.warning("DeepSeek JSON parse failed, using mock fallback: %s", exc)
        return fallback_data
