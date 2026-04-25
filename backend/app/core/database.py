import os

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker


# 数据库地址来自环境变量，默认写入 backend/data/app.db。
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/app.db")


def ensure_sqlite_dir(database_url: str) -> None:
    # SQLite 文件数据库需要提前创建目录，避免首次启动时报路径不存在。
    if not database_url.startswith("sqlite:///"):
        return

    db_path = database_url.replace("sqlite:///", "", 1)
    db_dir = os.path.dirname(db_path)
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)


ensure_sqlite_dir(DATABASE_URL)

# SQLite 需要 check_same_thread=False，便于 FastAPI 请求线程复用连接。
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    # FastAPI 依赖：每个请求创建独立 Session，请求结束后关闭。
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
