from fastapi import APIRouter


router = APIRouter(prefix="/analytics")


@router.get("/overview")
def get_analytics_overview():
    # 增长分析接口：返回 mock 投放数据、图表数据和 AI 优化建议。
    return {
        "code": 0,
        "message": "success",
        "data": {
            "metrics": {
                "impressions": 1285000,
                "ctr": 4.8,
                "cvr": 7.2,
                "spend": 18600,
                "revenue": 52680,
                "roi": 2.83,
            },
            "roiTrend": [
                {"date": "Mon", "roi": 2.1},
                {"date": "Tue", "roi": 2.35},
                {"date": "Wed", "roi": 2.52},
                {"date": "Thu", "roi": 2.41},
                {"date": "Fri", "roi": 2.83},
                {"date": "Sat", "roi": 3.12},
                {"date": "Sun", "roi": 2.96},
            ],
            "marketPerformance": [
                {"market": "北美", "revenue": 24800, "spend": 7600, "roi": 3.26},
                {"market": "东南亚", "revenue": 11600, "spend": 5200, "roi": 2.23},
                {"market": "日本", "revenue": 7200, "spend": 3100, "roi": 2.32},
                {"market": "韩国", "revenue": 5400, "spend": 2100, "roi": 2.57},
                {"market": "中东", "revenue": 3680, "spend": 600, "roi": 6.13},
            ],
            "creativeCtr": [
                {"creative": "强冲突钩子", "ctr": 6.2},
                {"creative": "身份反转", "ctr": 5.4},
                {"creative": "情绪崩溃", "ctr": 4.6},
                {"creative": "证据特写", "ctr": 4.2},
                {"creative": "复仇宣言", "ctr": 3.8},
            ],
            "suggestions": [
                "北美市场 ROI 高，建议增加预算，并优先放量强冲突钩子素材。",
                "东南亚点击率高但转化低，建议优化落地页首屏和付费引导。",
                "前 3 秒强冲突钩子表现最好，建议加大测试并缩短铺垫。",
            ],
        },
    }
