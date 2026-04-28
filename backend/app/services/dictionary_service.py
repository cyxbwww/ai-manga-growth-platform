"""业务字典服务。

当前先使用后端静态字典集中管理市场、语言、题材、阶段等选项；
后续如果需要运营后台维护，可平滑升级为数据库字典表或配置中心。
"""

DICTIONARIES = {
    "markets": [
        {"label": "中国大陆", "value": "中国大陆"},
        {"label": "北美", "value": "北美"},
        {"label": "东南亚", "value": "东南亚"},
        {"label": "日本", "value": "日本"},
        {"label": "韩国", "value": "韩国"},
        {"label": "中东", "value": "中东"},
        {"label": "欧洲", "value": "欧洲"},
        {"label": "拉美", "value": "拉美"},
    ],
    "languages": [
        {"label": "中文（zh-CN）", "value": "zh-CN"},
        {"label": "英文（en-US）", "value": "en-US"},
        {"label": "日文（ja-JP）", "value": "ja-JP"},
        {"label": "韩文（ko-KR）", "value": "ko-KR"},
        {"label": "泰文（th-TH）", "value": "th-TH"},
        {"label": "印尼文（id-ID）", "value": "id-ID"},
        {"label": "阿拉伯文（ar-SA）", "value": "ar-SA"},
        {"label": "西班牙文（es-ES）", "value": "es-ES"},
    ],
    "genres": [
        {"label": "都市逆袭", "value": "都市逆袭"},
        {"label": "情感爽剧", "value": "情感爽剧"},
        {"label": "女性成长", "value": "女性成长"},
        {"label": "甜宠", "value": "甜宠"},
        {"label": "悬疑", "value": "悬疑"},
        {"label": "复仇", "value": "复仇"},
    ],
    "project_stages": [
        {"label": "策划中", "value": "planning"},
        {"label": "剧本中", "value": "scripting"},
        {"label": "分镜中", "value": "storyboard"},
        {"label": "本地化中", "value": "localization"},
        {"label": "素材制作中", "value": "material"},
        {"label": "投放中", "value": "launch"},
        {"label": "已完成", "value": "completed"},
    ],
    "project_statuses": [
        {"label": "进行中", "value": "active"},
        {"label": "已暂停", "value": "paused"},
        {"label": "已完成", "value": "completed"},
        {"label": "已归档", "value": "archived"},
    ],
    "priorities": [
        {"label": "高", "value": "high"},
        {"label": "中", "value": "medium"},
        {"label": "低", "value": "low"},
    ],
}


def get_all_dictionaries():
    return DICTIONARIES


def get_dictionary(dict_type: str):
    return DICTIONARIES.get(dict_type)
