from datetime import datetime, time

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.ad_material import AdMaterial
from app.models.content_plan import ContentPlan
from app.models.localization import Localization
from app.models.script_polish import ScriptPolish
from app.models.storyboard import Storyboard


router = APIRouter(prefix="/dashboard")


def count_today(db: Session, model) -> int:
    # 今日统计：以本地日期 00:00 为起点统计各模块生成数量。
    today_start = datetime.combine(datetime.now().date(), time.min)
    return db.query(model).filter(model.created_at >= today_start).count()


@router.get("/summary")
def get_dashboard_summary(db: Session = Depends(get_db)):
    # 看板汇总接口：从 SQLite 读取真实生成记录统计。
    today_content_plans = count_today(db, ContentPlan)
    today_script_polishes = count_today(db, ScriptPolish)
    today_storyboards = count_today(db, Storyboard)
    today_localizations = count_today(db, Localization)
    today_ad_materials = count_today(db, AdMaterial)
    total_records = (
        db.query(ContentPlan).count()
        + db.query(ScriptPolish).count()
        + db.query(Storyboard).count()
        + db.query(Localization).count()
        + db.query(AdMaterial).count()
    )

    return {
        "code": 0,
        "message": "success",
        "data": {
            "todayContentPlans": today_content_plans,
            "todayScriptPolishes": today_script_polishes,
            "todayStoryboards": today_storyboards,
            "todayLocalizations": today_localizations,
            "todayAdMaterials": today_ad_materials,
            "totalRecords": total_records,
        },
    }
