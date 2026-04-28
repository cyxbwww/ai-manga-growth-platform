from datetime import datetime

from sqlalchemy.orm import Session

from app.models.short_drama_project import ShortDramaProject


def advance_project_stage(db: Session, project_id: int | None, next_stage: str) -> None:
    # 生产链路状态流转：生成成功后轻量推进项目阶段；失败不影响 AI 生成结果返回。
    if not project_id:
        return

    try:
        project = db.query(ShortDramaProject).filter(ShortDramaProject.id == project_id).first()
        if not project:
            print(f"项目阶段更新跳过：project_id={project_id} 不存在")
            return
        project.stage = next_stage
        project.updated_at = datetime.now()
        db.commit()
    except Exception as exc:
        db.rollback()
        print(f"项目阶段更新失败，已忽略：project_id={project_id}, next_stage={next_stage}, error={exc}")
