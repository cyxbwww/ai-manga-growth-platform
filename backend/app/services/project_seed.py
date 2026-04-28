from app.core.database import SessionLocal
from app.models.short_drama_episode import ShortDramaEpisode
from app.models.short_drama_project import ShortDramaProject


DEMO_PROJECTS = [
    {
        "name": "重生后我成了集团继承人",
        "genre": "都市逆袭",
        "target_market": "东南亚",
        "language": "zh-CN",
        "episode_count": 60,
        "stage": "storyboard",
        "description": "面向东南亚市场的都市逆袭短剧，强调身份反转和强情绪冲突。",
        "owner": "内容组A",
        "priority": "high",
        "status": "active",
    },
    {
        "name": "离婚后前夫跪求复合",
        "genre": "情感爽剧",
        "target_market": "中国大陆",
        "language": "zh-CN",
        "episode_count": 80,
        "stage": "material",
        "description": "面向国内投流场景的情感爽剧，突出前三秒冲突和高转化素材。",
        "owner": "增长组B",
        "priority": "medium",
        "status": "active",
    },
    {
        "name": "她从东南亚爆红归来",
        "genre": "女性成长",
        "target_market": "北美",
        "language": "en-US",
        "episode_count": 45,
        "stage": "localization",
        "description": "面向海外发行的女性成长短剧，重点验证本地化和多语言素材生产。",
        "owner": "出海组C",
        "priority": "medium",
        "status": "active",
    },
]

DEMO_EPISODES_BY_PROJECT = {
    "重生后我成了集团继承人": [
        ("重生回到订婚宴", "女主回到命运转折点，发现订婚宴背后隐藏的夺权计划。"),
        ("识破渣男计划", "女主利用前世记忆拆穿渣男布局，并第一次掌握主动权。"),
        ("进入集团董事会", "女主以继承人身份进入董事会，和反派阵营正面交锋。"),
    ],
    "离婚后前夫跪求复合": [
        ("离婚现场爆发", "女主在离婚现场公开关键证据，反转被动局面。"),
        ("前夫公开挽回", "前夫意识到真相后试图挽回，但女主已经完成自我觉醒。"),
        ("新身份反击", "女主以全新身份回归，开始反击曾经伤害她的人。"),
    ],
    "她从东南亚爆红归来": [
        ("海外爆红开场", "女主在海外短视频平台爆红，引发国内外团队关注。"),
        ("本地化危机", "团队发现直译内容无法打动目标市场，开始调整表达方式。"),
        ("逆风翻盘", "女主用更适合海外市场的表达完成传播反击。"),
    ],
}


def seed_short_drama_projects() -> None:
    # 面试演示数据：只在项目表为空时插入，避免每次启动重复创建。
    db = SessionLocal()
    try:
        if db.query(ShortDramaProject).count() == 0:
            db.add_all([ShortDramaProject(**item) for item in DEMO_PROJECTS])
            db.commit()

        # 面试演示分集数据：只在分集表为空时插入少量样例，避免分集列表首次打开是空白。
        if db.query(ShortDramaEpisode).count() == 0:
            episodes = []
            projects = db.query(ShortDramaProject).all()
            for project in projects:
                demo_items = DEMO_EPISODES_BY_PROJECT.get(project.name)
                if not demo_items:
                    continue
                for index, (title, summary) in enumerate(demo_items, start=1):
                    episodes.append(
                        ShortDramaEpisode(
                            project_id=project.id,
                            episode_no=index,
                            title=title,
                            summary=summary,
                            stage=project.stage if project.stage in {"planning", "scripting", "storyboard", "localization", "media", "completed"} else "planning",
                            status="active",
                            script_status="completed" if index == 1 else "pending",
                            storyboard_status="completed" if project.stage in {"storyboard", "localization", "material", "launch", "completed"} and index == 1 else "pending",
                            localization_status="completed" if project.stage in {"localization", "material", "launch", "completed"} and index == 1 else "pending",
                            media_status="pending",
                        )
                    )
            db.add_all(episodes)
            db.commit()
    finally:
        db.close()
