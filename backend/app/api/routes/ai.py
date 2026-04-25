from fastapi import APIRouter

from app.core.config import AI_API_KEY, AI_BASE_URL, AI_MODEL, AI_PROVIDER


router = APIRouter(prefix="/ai")


@router.get("/status")
def get_ai_status():
    # AI 状态接口：只返回是否配置 Key，不暴露真实 API Key。
    has_api_key = bool(AI_API_KEY)
    return {
        "code": 0,
        "message": "success",
        "data": {
            "provider": AI_PROVIDER,
            "model": AI_MODEL,
            "enabled": AI_PROVIDER == "deepseek" and has_api_key,
            "hasApiKey": has_api_key,
            "baseUrl": AI_BASE_URL,
        },
    }
