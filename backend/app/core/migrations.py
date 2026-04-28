from sqlalchemy import inspect, text


def ensure_column(engine, table_name: str, column_name: str, column_sql: str) -> None:
    # 轻量字段补齐：SQLite 旧表不会被 SQLAlchemy create_all 自动加列，这里按需 ALTER TABLE。
    inspector = inspect(engine)
    table_names = inspector.get_table_names()
    if table_name not in table_names:
        return

    columns = {column["name"] for column in inspector.get_columns(table_name)}
    if column_name in columns:
        return

    with engine.begin() as connection:
        connection.execute(text(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_sql}"))


def ensure_pipeline_columns(engine) -> None:
    # 全链路 ID 字段均允许为空，保证旧历史数据继续可读。
    ensure_column(engine, "content_plans", "project_id", "INTEGER")

    ensure_column(engine, "script_polishes", "project_id", "INTEGER")
    ensure_column(engine, "script_polishes", "content_plan_id", "INTEGER")
    ensure_column(engine, "script_polishes", "language", "VARCHAR(50)")

    ensure_column(engine, "storyboards", "project_id", "INTEGER")
    ensure_column(engine, "storyboards", "episode_id", "INTEGER")
    ensure_column(engine, "storyboards", "episode_no", "INTEGER")
    ensure_column(engine, "storyboards", "content_plan_id", "INTEGER")
    ensure_column(engine, "storyboards", "script_polish_id", "INTEGER")

    ensure_column(engine, "localizations", "project_id", "INTEGER")
    ensure_column(engine, "localizations", "episode_id", "INTEGER")
    ensure_column(engine, "localizations", "episode_no", "INTEGER")
    ensure_column(engine, "localizations", "content_plan_id", "INTEGER")
    ensure_column(engine, "localizations", "script_polish_id", "INTEGER")
    ensure_column(engine, "localizations", "storyboard_id", "INTEGER")

    ensure_column(engine, "ad_materials", "project_id", "INTEGER")
    ensure_column(engine, "ad_materials", "episode_id", "INTEGER")
    ensure_column(engine, "ad_materials", "episode_no", "INTEGER")
    ensure_column(engine, "ad_materials", "content_plan_id", "INTEGER")
    ensure_column(engine, "ad_materials", "script_polish_id", "INTEGER")
    ensure_column(engine, "ad_materials", "storyboard_id", "INTEGER")
    ensure_column(engine, "ad_materials", "localization_id", "INTEGER")

    ensure_column(engine, "media_assets", "project_id", "INTEGER")
    ensure_column(engine, "media_assets", "episode_id", "INTEGER")
    ensure_column(engine, "media_assets", "episode_no", "INTEGER")
