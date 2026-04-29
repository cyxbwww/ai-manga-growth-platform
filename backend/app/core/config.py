import os


# API 前缀：默认 /api，可通过 backend/.env 覆盖。
API_PREFIX = os.getenv("API_PREFIX", "/api")

# Debug 开关：字符串环境变量转为布尔值，便于本地和生产切换。
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
DEBUG_LLM_RESPONSE = os.getenv("DEBUG_LLM_RESPONSE", "false").lower() == "true"
ENABLE_STORYBOARD_MOCK_FALLBACK = os.getenv("ENABLE_STORYBOARD_MOCK_FALLBACK", "false").lower() == "true"

# 演示数据开关：默认开启，保证面试演示删除数据库后仍能自动生成项目和分集样例。
ENABLE_DEMO_SEED = os.getenv("ENABLE_DEMO_SEED", "true").lower() == "true"

# AI Provider 配置：mock 强制走本地 mock，deepseek 优先调用真实模型。
AI_PROVIDER = os.getenv("AI_PROVIDER", "mock").lower()
AI_API_KEY = os.getenv("AI_API_KEY", "")
AI_BASE_URL = os.getenv("AI_BASE_URL", "https://api.deepseek.com")
AI_MODEL = os.getenv("AI_MODEL", "deepseek-v4-flash")
AI_TEMPERATURE = float(os.getenv("AI_TEMPERATURE", "0.7"))
AI_MAX_TOKENS = int(os.getenv("AI_MAX_TOKENS", "3000"))
STORYBOARD_LLM_MAX_TOKENS = int(os.getenv("STORYBOARD_LLM_MAX_TOKENS", "6000"))
AI_TIMEOUT = int(os.getenv("AI_TIMEOUT", "60"))

# 媒体上传配置：真实模式使用 S3 / S3 兼容 OSS，mock 模式用于本地演示。
MEDIA_PROVIDER = os.getenv("MEDIA_PROVIDER", "mock").lower()
AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID", "")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "")
AWS_REGION = os.getenv("AWS_REGION", "ap-southeast-1")
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET", "")
AWS_S3_ENDPOINT_URL = os.getenv("AWS_S3_ENDPOINT_URL", "")
AWS_S3_PUBLIC_BASE_URL = os.getenv("AWS_S3_PUBLIC_BASE_URL", "")
S3_UPLOAD_PREFIX = os.getenv("S3_UPLOAD_PREFIX", "media").strip("/")
S3_PRESIGNED_EXPIRE_SECONDS = int(os.getenv("S3_PRESIGNED_EXPIRE_SECONDS", "3600"))
S3_ADDRESSING_STYLE = os.getenv("S3_ADDRESSING_STYLE", "path")
S3_SIGNATURE_VERSION = os.getenv("S3_SIGNATURE_VERSION", "s3v4")
