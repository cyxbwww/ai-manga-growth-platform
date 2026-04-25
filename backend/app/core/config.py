import os


# API 前缀：默认 /api，可通过 backend/.env 覆盖。
API_PREFIX = os.getenv("API_PREFIX", "/api")

# Debug 开关：字符串环境变量转为布尔值，便于本地和生产切换。
DEBUG = os.getenv("DEBUG", "false").lower() == "true"

# AI Provider 配置：mock 强制走本地 mock，deepseek 优先调用真实模型。
AI_PROVIDER = os.getenv("AI_PROVIDER", "mock").lower()
AI_API_KEY = os.getenv("AI_API_KEY", "")
AI_BASE_URL = os.getenv("AI_BASE_URL", "https://api.deepseek.com")
AI_MODEL = os.getenv("AI_MODEL", "deepseek-v4-flash")
AI_TEMPERATURE = float(os.getenv("AI_TEMPERATURE", "0.7"))
AI_MAX_TOKENS = int(os.getenv("AI_MAX_TOKENS", "3000"))
AI_TIMEOUT = int(os.getenv("AI_TIMEOUT", "60"))
