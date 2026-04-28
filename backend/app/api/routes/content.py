import json
import logging
import re
from typing import Any

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.content_plan import ContentPlan
from app.services.ai_service import request_ai_text
from app.services.dictionary_service import language_prompt_name, normalize_language_code
from app.services.project_flow import advance_project_stage


router = APIRouter(prefix="/content")
logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "你是一个 AI短剧内容生产助手，擅长短剧内容策划、剧本打磨、分镜拆解、多语种本地化和海外广告投放素材生成。"
    "你必须严格返回 JSON 对象，不要返回 Markdown，不要解释，不要输出代码块。"
)

LANGUAGE_RULES = """
【多语言输出规则】
1. 返回结构必须包含 bilingual.zh 和 bilingual.target。
2. bilingual.zh 中所有字段必须使用中文。
3. bilingual.target 中所有字段必须使用目标语言 target_language 对应的语言。
4. 即使目标市场是北美、目标语言是 en-US，bilingual.zh 也必须是中文。
5. 如果 target_language 是 en-US，bilingual.target 必须是英文。
6. 如果 target_language 是 ja-JP，bilingual.target 必须是日文。
7. 如果 target_language 是 ko-KR，bilingual.target 必须是韩文。
8. 如果 target_language 是 th-TH，bilingual.target 必须是泰文。
9. 如果 target_language 是 id-ID，bilingual.target 必须是印尼文。
10. 如果 target_language 是 ar-SA，bilingual.target 必须是阿拉伯文。
11. 如果 target_language 是 es-ES，bilingual.target 必须是西班牙文。
12. 不允许把英文标题、英文台词、英文完整句子写进 bilingual.zh。
13. 不允许把中文内容直接复制到 bilingual.target，除非目标语言就是 zh-CN。
14. 平台名 TikTok、YouTube Shorts、Instagram Reels、Facebook Watch 可以保留原文。
15. 中文旁白必须写中文；英文旁白只出现在 en-US target 中；其它目标语言旁白必须使用对应目标语言。
16. 不要输出 Markdown，严格输出 JSON。
"""

CONTENT_FIELDS = [
    "title",
    "positioning",
    "targetAudience",
    "coreConflict",
    "emotionHook",
    "openingHook",
    "highlights",
    "suggestions",
]

PLATFORM_NAMES = ["TikTok", "YouTube Shorts", "Instagram Reels", "Facebook Watch"]

TARGET_LANGUAGE_NAMES = {
    "zh-CN": "中文",
    "en-US": "英文",
    "ja-JP": "日文",
    "ko-KR": "韩文",
    "th-TH": "泰文",
    "id-ID": "印尼文",
    "ar-SA": "阿拉伯文",
    "es-ES": "西班牙文",
}


class ContentPlanRequest(BaseModel):
    # 内容策划请求字段保持与前端和历史版本兼容。
    project_id: int | None = None
    projectName: str
    genre: str
    market: str
    language: str
    duration: str
    sellingPoint: str


def target_mock_fields(payload: ContentPlanRequest, language_code: str) -> dict[str, Any]:
    if language_code == "zh-CN":
        return {}
    if language_code == "ja-JP":
        return {
            "title": f"{payload.projectName} - {payload.market}向け縦型ショートドラマ企画",
            "positioning": "強い対立、速い反転、明確な感情解放を軸にした縦型ショートドラマ。",
            "targetAudience": "短時間で人物関係と爽快な反撃を理解したい若年層のショート動画視聴者。",
            "coreConflict": "主人公は親しい関係の中で裏切られ、証拠と行動で立場を逆転していく。",
            "emotionHook": "屈辱、誤解、裏切りから始め、正体の開示と反撃で感情を解放する。",
            "openingHook": "冒頭三秒で公開の場の否定を見せ、直後に隠された正体を示唆する一言を置く。",
            "highlights": ["隠された証拠の提示", "裏切りの記憶による感情の揺れ", "敗北に見せかけた逆転"],
            "suggestions": ["一話では一つの衝突に絞る。", "説明台詞を減らし行動で関係性を見せる。", "各話の最後に追視聴したくなる疑問を残す。"],
        }
    if language_code == "ko-KR":
        return {
            "title": f"{payload.projectName} - {payload.market} 타깃 숏폼 드라마 기획",
            "positioning": "강한 갈등, 빠른 반전, 분명한 감정 해소를 중심으로 한 세로형 숏폼 드라마.",
            "targetAudience": "짧은 시간 안에 관계와 반격의 쾌감을 이해하고 싶은 숏폼 시청자.",
            "coreConflict": "주인공은 가까운 관계에서 배신당하고, 증거와 행동으로 상황을 뒤집는다.",
            "emotionHook": "모욕과 오해로 감정 압박을 만들고 정체 공개와 반격으로 해소한다.",
            "openingHook": "첫 3초에 공개적인 거절을 보여주고 숨겨진 정체를 암시하는 한마디를 넣는다.",
            "highlights": ["숨겨진 증거 공개", "배신당한 기억의 감정 자극", "패배처럼 보이는 순간의 반전"],
            "suggestions": ["한 회차에는 하나의 핵심 갈등만 둔다.", "설명보다 행동과 결과로 관계를 보여준다.", "마지막에는 다음 회를 보게 만드는 의문을 남긴다."],
        }
    if language_code == "th-TH":
        return {
            "title": f"{payload.projectName} - แผนซีรีส์สั้นสำหรับตลาด {payload.market}",
            "positioning": "ซีรีส์สั้นแนวตั้งที่เน้นความขัดแย้งแรง จังหวะเร็ว และการพลิกสถานการณ์ที่ชัดเจน",
            "targetAudience": "ผู้ชมวิดีโอสั้นที่ต้องการเข้าใจความสัมพันธ์และจุดสะใจได้อย่างรวดเร็ว",
            "coreConflict": "ตัวเอกถูกหักหลังจากคนใกล้ตัว แล้วใช้หลักฐานและการตัดสินใจพลิกเกมกลับมา",
            "emotionHook": "เริ่มด้วยการดูถูก ความเข้าใจผิด และการทรยศ ก่อนปล่อยอารมณ์ด้วยการเปิดเผยตัวตน",
            "openingHook": "สามวินาทีแรกต้องเห็นตัวเอกถูกปฏิเสธต่อหน้า แล้วตามด้วยประโยคที่บอกใบ้ตัวตนที่ซ่อนอยู่",
            "highlights": ["หลักฐานลับถูกเปิดเผย", "ความเจ็บปวดจากการถูกทอดทิ้ง", "จังหวะที่เหมือนแพ้แต่กลับพลิกเกม"],
            "suggestions": ["แต่ละตอนควรมีความขัดแย้งหลักเพียงหนึ่งเรื่อง", "ใช้การกระทำแทนบทอธิบายยาว", "จบตอนด้วยคำถามหรือวิกฤตใหม่"],
        }
    if language_code == "id-ID":
        return {
            "title": f"{payload.projectName} - Rencana drama pendek untuk pasar {payload.market}",
            "positioning": "Drama vertikal dengan konflik kuat, ritme cepat, dan pembalikan nasib yang mudah dipahami.",
            "targetAudience": "Penonton video pendek yang menyukai emosi kuat, pengkhianatan, dan balasan yang memuaskan.",
            "coreConflict": "Tokoh utama dikhianati oleh orang terdekat, lalu memakai bukti dan strategi untuk merebut kendali.",
            "emotionHook": "Mulai dari penghinaan dan salah paham, lalu lepaskan emosi melalui pengungkapan identitas dan serangan balik.",
            "openingHook": "Dalam tiga detik pertama, tampilkan penolakan publik dan satu kalimat yang mengisyaratkan rahasia tokoh utama.",
            "highlights": ["Bukti tersembunyi terungkap", "Luka emosional karena pengkhianatan", "Momen kalah yang berubah menjadi kemenangan"],
            "suggestions": ["Fokus pada satu konflik utama di setiap episode.", "Kurangi dialog penjelasan dan gunakan aksi.", "Akhiri episode dengan krisis baru."],
        }
    if language_code == "ar-SA":
        return {
            "title": f"{payload.projectName} - خطة مسلسل قصير لسوق {payload.market}",
            "positioning": "دراما عمودية قصيرة تعتمد على صراع قوي وإيقاع سريع وانقلاب واضح في موازين القوة.",
            "targetAudience": "مشاهدو الفيديوهات القصيرة الذين يفضلون العاطفة القوية والخيانة والانتقام الواضح.",
            "coreConflict": "تتعرض البطلة للخيانة من أقرب الناس إليها، ثم تستخدم الأدلة والذكاء لتستعيد السيطرة.",
            "emotionHook": "تبدأ القصة بالإهانة وسوء الفهم، ثم تمنح الجمهور تفريغا عاطفيا عبر كشف الهوية والرد الحاسم.",
            "openingHook": "في الثواني الثلاث الأولى نرى رفضا علنيا للبطلة، ثم جملة تكشف أن لديها سرا يغير الموقف.",
            "highlights": ["كشف دليل مخفي", "جرح عاطفي بسبب الخيانة", "لحظة تبدو كهزيمة ثم تتحول إلى انتصار"],
            "suggestions": ["اجعل كل حلقة تدور حول صراع رئيسي واحد.", "استخدم الفعل والنتيجة بدلا من الشرح الطويل.", "اختم كل حلقة بأزمة أو سؤال جديد."],
        }
    if language_code == "es-ES":
        return {
            "title": f"{payload.projectName} - Plan de drama corto para el mercado {payload.market}",
            "positioning": "Drama vertical con conflicto fuerte, ritmo rápido y giros claros de poder emocional.",
            "targetAudience": "Usuarios de videos cortos que buscan traición, tensión emocional y una revancha satisfactoria.",
            "coreConflict": "La protagonista es traicionada por alguien cercano y usa pruebas y estrategia para recuperar el control.",
            "emotionHook": "La historia empieza con humillación y malentendidos, y libera emoción mediante una revelación y un contraataque.",
            "openingHook": "En los primeros tres segundos, la protagonista es rechazada en público y una frase insinúa su identidad oculta.",
            "highlights": ["Prueba oculta revelada", "Herida emocional por la traición", "Derrota aparente que se convierte en victoria"],
            "suggestions": ["Mantén un conflicto principal por episodio.", "Reduce la explicación y muestra relaciones con acciones.", "Cierra cada episodio con una nueva crisis."],
        }
    return {
        "title": f"{payload.projectName} - {payload.market} short drama plan",
        "positioning": f"A vertical short drama for the {payload.market} market with fast reversals and clear emotional stakes.",
        "targetAudience": "Short-video viewers aged 18-34 who respond to high emotion, quick reversals, and clear character stakes.",
        "coreConflict": "The heroine is publicly underestimated, then uses hidden leverage to turn humiliation into a powerful comeback.",
        "emotionHook": "Open with betrayal and public pressure, then release emotion through a reveal, proof, and decisive action.",
        "openingHook": "Start with a public rejection in the first three seconds, followed by one line that hints at a hidden identity.",
        "highlights": ["Hidden proof is revealed", "A painful betrayal memory", "A defeat that turns into a comeback"],
        "suggestions": ["Keep one main conflict per episode.", "Use action instead of long explanatory dialogue.", "End with a strong cliffhanger."],
    }


def target_language_name(language_code: str) -> str:
    return TARGET_LANGUAGE_NAMES.get(normalize_language_code(language_code) or language_code, language_prompt_name(language_code))


def build_content_plan_result(payload: ContentPlanRequest) -> dict:
    # fallback 只生成结构化纯净版本，不做任何固定短句替换。
    language_code = normalize_language_code(payload.language) or payload.language
    zh = {
        "title": f"{payload.projectName} - {payload.market}{payload.duration}短剧策划",
        "positioning": f"面向{payload.market}市场的{payload.genre}竖屏短剧，内部审核版本始终使用中文，强调强冲突、快反转和清晰情绪价值。",
        "targetAudience": "18-34岁短视频用户，偏好强情绪、快反转、明确爽点和可快速理解的人物关系。",
        "coreConflict": "主角在亲密关系或身份关系中被低估，随后用隐藏资源和关键证据完成反击，形成压迫到逆转的强对比。",
        "emotionHook": "用背叛、羞辱、误解或错失制造情绪压力，再用身份揭晓和主动反击释放情绪。",
        "openingHook": "开场三秒直接给出冲突现场：主角被当众否定，同时抛出一句带身份反转的信息。",
        "highlights": [
            "爽点：弱势主角亮出隐藏身份或关键证据",
            "泪点：主角短暂回忆被家人或恋人抛弃的瞬间",
            "反转点：观众以为主角失败，实际她早已掌握主动权",
        ],
        "platforms": ["TikTok", "YouTube Shorts", "Instagram Reels", "Facebook Watch"],
        "suggestions": [
            f"{payload.duration}版本建议控制在一个核心冲突内，避免支线过多。",
            f"{payload.market}市场表达要减少解释性台词，优先使用动作和结果呈现人物关系。",
            "结尾需要保留追更悬念，方便后续分集大纲、分镜和广告素材继续承接。",
        ],
    }
    target = {**zh, "language": language_code} if language_code == "zh-CN" else {"language": language_code, **target_mock_fields(payload, language_code)}
    target["platforms"] = ["TikTok", "YouTube Shorts", "Instagram Reels", "Facebook Watch"]
    return {**zh, "bilingual": {"zh": zh, "target": target}}


def build_user_prompt(payload: ContentPlanRequest, strict_language_retry: bool = False) -> str:
    language_code = normalize_language_code(payload.language) or payload.language
    language_name = target_language_name(language_code)
    retry_rule = "这是一次语言校验失败后的重试，请特别检查 bilingual.zh 只能写中文，bilingual.target 只能写目标语言。" if strict_language_retry else ""
    return f"""
请根据以下用户输入生成 AI短剧内容策划方案。

项目名称：{payload.projectName}
短剧题材：{payload.genre}
目标市场：{payload.market}
target_language：{language_code}
目标语言名称：{language_name}
单集目标时长：{payload.duration}
核心卖点：{payload.sellingPoint}

{LANGUAGE_RULES}
{retry_rule}

业务要求：
1. 适合 AI短剧，结果适合后续分镜制作、分集大纲生成和广告投放。
2. 根据目标市场做内容定位，但 bilingual.zh 始终使用中文。
3. 强调前三秒钩子、冲突、反转和情绪价值。

只返回 JSON 对象，字段必须严格如下：
{{
  "title": "中文 string",
  "positioning": "中文 string",
  "targetAudience": "中文 string",
  "coreConflict": "中文 string",
  "emotionHook": "中文 string",
  "openingHook": "中文 string",
  "highlights": ["中文 string"],
  "platforms": ["TikTok", "YouTube Shorts", "Instagram Reels", "Facebook Watch"],
  "suggestions": ["中文 string"],
  "bilingual": {{
    "zh": {{
      "title": "中文 string",
      "positioning": "中文 string",
      "targetAudience": "中文 string",
      "coreConflict": "中文 string",
      "emotionHook": "中文 string",
      "openingHook": "中文 string",
      "highlights": ["中文 string"],
      "platforms": ["TikTok", "YouTube Shorts", "Instagram Reels", "Facebook Watch"],
      "suggestions": ["中文 string"]
    }},
    "target": {{
      "language": "{language_code}",
      "title": "{language_name} string",
      "positioning": "{language_name} string",
      "targetAudience": "{language_name} string",
      "coreConflict": "{language_name} string",
      "emotionHook": "{language_name} string",
      "openingHook": "{language_name} string",
      "highlights": ["{language_name} string"],
      "platforms": ["TikTok", "YouTube Shorts", "Instagram Reels", "Facebook Watch"],
      "suggestions": ["{language_name} string"]
    }}
  }}
}}
"""


def collect_text(value: Any) -> str:
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        return "\n".join(collect_text(item) for item in value)
    if isinstance(value, dict):
        return "\n".join(collect_text(item) for item in value.values())
    return ""


def plan_language_text(fields: dict[str, Any]) -> str:
    parts = [collect_text(fields.get(key)) for key in CONTENT_FIELDS]
    text = "\n".join(parts)
    for platform in PLATFORM_NAMES:
        text = text.replace(platform, "")
    return text


def count_pattern(pattern: str, text: str) -> int:
    return len(re.findall(pattern, text))


def has_english_complete_sentence(value: str) -> bool:
    cleaned = value
    for platform in PLATFORM_NAMES:
        cleaned = cleaned.replace(platform, "")
    if re.search(r"\b[A-Za-z]+(?:\s+[A-Za-z]+){3,}[.!?]", cleaned):
        return True
    return bool(re.search(r"[.!?]", cleaned) and count_pattern(r"\b[A-Za-z]{2,}\b", cleaned) >= 4)


def is_mostly_chinese_text(value: str) -> bool:
    if has_english_complete_sentence(value):
        return False
    chinese_count = count_pattern(r"[\u4e00-\u9fff]", value)
    english_words = count_pattern(r"\b[A-Za-z]{3,}\b", value)
    return chinese_count >= 20 and chinese_count >= english_words * 2


def has_too_much_chinese(value: str) -> bool:
    chinese_count = count_pattern(r"[\u4e00-\u9fff]", value)
    latin_words = count_pattern(r"\b[A-Za-z]{3,}\b", value)
    total_letters = count_pattern(r"[A-Za-z\u3040-\u30ff\uac00-\ud7af\u0e00-\u0e7f\u0600-\u06ff]", value)
    return chinese_count >= 20 and chinese_count > max(total_letters, latin_words) * 0.35


def is_mostly_target_language_text(value: str, language_code: str) -> bool:
    language_code = normalize_language_code(language_code) or language_code
    if language_code == "zh-CN":
        return is_mostly_chinese_text(value)
    if language_code == "ja-JP":
        return count_pattern(r"[\u3040-\u30ff]", value) >= 8
    if language_code == "ko-KR":
        return count_pattern(r"[\uac00-\ud7af]", value) >= 8
    if language_code == "th-TH":
        return count_pattern(r"[\u0e00-\u0e7f]", value) >= 8
    if language_code == "ar-SA":
        return count_pattern(r"[\u0600-\u06ff]", value) >= 8
    if has_too_much_chinese(value):
        return False
    if language_code == "en-US":
        return count_pattern(r"\b[A-Za-z]{3,}\b", value) >= 20
    if language_code == "es-ES":
        spanish_markers = count_pattern(r"[áéíóúñÁÉÍÓÚÑ¿¡]", value)
        spanish_words = count_pattern(r"\b(el|la|los|las|una|para|con|que|por|protagonista|conflicto|episodio|traición|revancha)\b", value.lower())
        return count_pattern(r"\b[A-Za-zÁÉÍÓÚÜÑáéíóúüñ]{3,}\b", value) >= 15 and (spanish_markers + spanish_words) >= 2
    if language_code == "id-ID":
        return count_pattern(r"\b[A-Za-z]{3,}\b", value) >= 15
    return bool(value.strip())


def validate_bilingual_plan_language(plan: dict[str, Any], target_language: str) -> bool:
    bilingual = plan.get("bilingual")
    if not isinstance(bilingual, dict):
        return False
    zh = bilingual.get("zh")
    target = bilingual.get("target")
    if not isinstance(zh, dict) or not isinstance(target, dict):
        return False

    zh_text = plan_language_text(zh)
    target_text = plan_language_text(target)
    if not is_mostly_chinese_text(zh_text):
        return False
    return is_mostly_target_language_text(target_text, target_language)


def parse_content_plan_json(content: str) -> dict[str, Any]:
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        start = content.find("{")
        end = content.rfind("}")
        if start >= 0 and end > start:
            return json.loads(content[start : end + 1])
        raise


def normalize_plan_shape(plan: dict[str, Any], language_code: str, fallback_data: dict[str, Any]) -> dict[str, Any]:
    bilingual = plan.get("bilingual") if isinstance(plan.get("bilingual"), dict) else {}
    zh = bilingual.get("zh") if isinstance(bilingual.get("zh"), dict) else None
    target = bilingual.get("target") if isinstance(bilingual.get("target"), dict) else None

    if not zh:
        zh = {key: plan.get(key, fallback_data["bilingual"]["zh"].get(key)) for key in fallback_data["bilingual"]["zh"].keys()}
    if not target:
        target = fallback_data["bilingual"]["target"]

    target["language"] = language_code
    zh["platforms"] = zh.get("platforms") or PLATFORM_NAMES
    target["platforms"] = target.get("platforms") or PLATFORM_NAMES

    normalized = {**zh, "bilingual": {"zh": zh, "target": target}}
    return normalized


def generate_content_plan_with_language_guard(payload: ContentPlanRequest, fallback_data: dict[str, Any]) -> dict[str, Any]:
    for attempt in range(2):
        content, error = request_ai_text(SYSTEM_PROMPT, build_user_prompt(payload, strict_language_retry=attempt > 0), response_format_json=True)
        if error or not content:
            logger.warning("内容策划 DeepSeek 不可用，已使用 fallback: %s", error)
            return fallback_data
        try:
            result = normalize_plan_shape(parse_content_plan_json(content), payload.language, fallback_data)
        except Exception as exc:
            logger.warning("内容策划 JSON 解析失败，%s", "已重试" if attempt == 0 else "已使用 fallback")
            if attempt == 0:
                continue
            return fallback_data
        if validate_bilingual_plan_language(result, payload.language):
            return result
        logger.warning("内容策划语言校验失败，%s。", "已重试" if attempt == 0 else "已使用 fallback")
    return fallback_data


@router.post("/plan")
def create_content_plan(payload: ContentPlanRequest, db: Session = Depends(get_db)):
    payload.language = normalize_language_code(payload.language) or payload.language
    fallback_data = build_content_plan_result(payload)
    result = generate_content_plan_with_language_guard(payload, fallback_data)

    record = ContentPlan(
        project_id=payload.project_id,
        project_name=payload.projectName,
        genre=payload.genre,
        market=payload.market,
        language=payload.language,
        duration=payload.duration,
        selling_point=payload.sellingPoint,
        result_json=json.dumps(result, ensure_ascii=False),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    advance_project_stage(db, payload.project_id, "scripting")

    return {"code": 0, "message": "success", "data": {"recordId": record.id, "project_id": payload.project_id, **result}}


@router.get("/plans")
def get_content_plan_history(
    project_id: int | None = Query(default=None),
    limit: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(ContentPlan)
    if project_id:
        query = query.filter(ContentPlan.project_id == project_id)
    records = query.order_by(ContentPlan.created_at.desc()).limit(limit).all()
    data = [
        {
            "id": item.id,
            "recordId": item.id,
            "project_id": item.project_id,
            "projectName": item.project_name,
            "genre": item.genre,
            "market": item.market,
            "language": normalize_language_code(item.language) or item.language,
            "duration": item.duration,
            "sellingPoint": item.selling_point,
            "result": json.loads(item.result_json),
            "createdAt": item.created_at.isoformat(),
        }
        for item in records
    ]
    return {"code": 0, "message": "success", "data": data}
