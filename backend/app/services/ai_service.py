import json

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


def generate_json(system_prompt: str, user_prompt: str, fallback_data: dict) -> dict:
    # mock 模式强制不调用外部模型，保证面试演示和本地开发稳定可用。
    if AI_PROVIDER != "deepseek":
        return fallback_data

    if not AI_API_KEY:
        # 不打印或返回真实 Key，只提示当前走 fallback。
        print("未配置 AI_API_KEY，使用 mock fallback")
        return fallback_data

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
            max_tokens=AI_MAX_TOKENS,
            response_format={"type": "json_object"},
        )
        content = response.choices[0].message.content
        if not content:
            print("DeepSeek 返回内容为空，使用 mock fallback")
            return fallback_data

        return json.loads(content)
    except json.JSONDecodeError as exc:
        print(f"DeepSeek JSON 解析失败，使用 mock fallback: {exc}")
        return fallback_data
    except Exception as exc:
        print(f"DeepSeek 调用失败，使用 mock fallback: {exc}")
        return fallback_data
