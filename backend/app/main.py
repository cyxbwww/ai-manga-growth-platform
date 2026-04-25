from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 启动时加载 backend/.env，确保后端配置来自环境变量。
load_dotenv()

from app import models  # noqa: F401
from app.api.routes.ads import router as ads_router
from app.api.routes.ai import router as ai_router
from app.api.routes.analytics import router as analytics_router
from app.api.routes.content import router as content_router
from app.api.routes.dashboard import router as dashboard_router
from app.api.routes.health import router as health_router
from app.api.routes.localization import router as localization_router
from app.api.routes.media import router as media_router
from app.api.routes.pipeline import router as pipeline_router
from app.api.routes.script import router as script_router
from app.api.routes.storyboard import router as storyboard_router
from app.core.config import API_PREFIX, DEBUG
from app.core.database import Base, engine
from app.core.migrations import ensure_pipeline_columns


# 自动创建表；旧 SQLite 表不会被 create_all 自动补列，因此再执行轻量字段补齐。
Base.metadata.create_all(bind=engine)
ensure_pipeline_columns(engine)

app = FastAPI(
    title="AI漫剧出海增长平台 Demo API",
    debug=DEBUG,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_origin_regex=r"http://(localhost|127\.0\.0\.1):\d+",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix=API_PREFIX)
app.include_router(dashboard_router, prefix=API_PREFIX)
app.include_router(content_router, prefix=API_PREFIX)
app.include_router(script_router, prefix=API_PREFIX)
app.include_router(storyboard_router, prefix=API_PREFIX)
app.include_router(localization_router, prefix=API_PREFIX)
app.include_router(media_router, prefix=API_PREFIX)
app.include_router(ads_router, prefix=API_PREFIX)
app.include_router(analytics_router, prefix=API_PREFIX)
app.include_router(ai_router, prefix=API_PREFIX)
app.include_router(pipeline_router, prefix=API_PREFIX)
