"""
keyboards.py — фабрики инлайн-клавиатур.
Всё меню строится здесь. Когда добавляешь новый контент,
правишь только этот файл + content/ папку.
"""
from telegram import InlineKeyboardButton as Btn, InlineKeyboardMarkup as Markup
from config import SUBJECTS, TEST_TYPES


def back(to: str) -> list:
    return [Btn("⬅️ Назад", callback_data=f"back_{to}")]


# ═══════════════════════ ГЛАВНОЕ МЕНЮ ═══════════════════════
def main_menu() -> Markup:
    return Markup([
        [Btn("📚 Сборники",            callback_data="menu_collections")],
        [Btn("📖 Сокращённые сборники", callback_data="menu_short")],
        [Btn("✏️ Тесты",               callback_data="menu_tests")],
        [Btn("📋 Шпаргалки",           callback_data="menu_cheat")],
        [Btn("🔗 Полезные ссылки",     callback_data="menu_links")],
        [Btn("👤 Личный кабинет",      callback_data="menu_cabinet")],
    ])


# ═══════════════════════ ВЫБОР ПРЕДМЕТА ═════════════════════
def subject_menu(section: str) -> Markup:
    rows = [[Btn(label, callback_data=f"{section}_sub_{key}")]
            for key, label in SUBJECTS.items()]
    rows.append([back("main")])
    return Markup(rows)


# ═══════════════════════ СБОРНИКИ ═══════════════════════════
def collections_list(subject: str, items: list) -> Markup:
    """
    items = [{"id":"math_col_001","title":"Сборник 2024"}, ...]
    """
    rows = [[Btn(f"📄 {i['title']}", callback_data=f"col_file_{i['id']}")] for i in items]
    rows.append([back(f"col_sub_{subject}")])
    return Markup(rows)


# ════════════════════ ТЕСТЫ: ТИП / ГОД / ЭТАП / ВАРИАНТ ════
def test_type_menu(subject: str) -> Markup:
    rows = [[Btn(label, callback_data=f"test_type_{subject}_{key}")]
            for key, label in TEST_TYPES.items()]
    rows.append([back(f"test_sub_{subject}")])
    return Markup(rows)


def test_years_menu(subject: str, ttype: str, years: list) -> Markup:
    rows = [[Btn(y, callback_data=f"test_year_{subject}_{ttype}_{y}")] for y in years]
    rows.append([back(f"test_type_{subject}_{ttype}")])
    return Markup(rows)


def test_stages_menu(subject: str, ttype: str, year: str, stages: list) -> Markup:
    labels = {"I": "I этап", "II": "II этап", "III": "III этап"}
    rows = [[Btn(labels.get(s, s), callback_data=f"test_stage_{subject}_{ttype}_{year}_{s}")]
            for s in stages]
    rows.append([back(f"test_year_{subject}_{ttype}_{year}")])
    return Markup(rows)


def test_variants_menu(subject: str, ttype: str, year: str, stage: str, variants: list) -> Markup:
    rows = [[Btn(f"Вариант {v}", callback_data=f"test_var_{subject}_{ttype}_{year}_{stage}_{v}")]
            for v in variants]
    rows.append([back(f"test_stage_{subject}_{ttype}_{year}_{stage}")])
    return Markup(rows)


# ════════════════════════ ВОПРОС В ТЕСТЕ ════════════════════
def question_buttons(q: dict, q_idx: int, total: int,
                     subject, ttype, year, stage, variant) -> Markup:
    """
    q = {type: "choice"|"input", options: {...}, id: N}
    """
    base = f"{subject}_{ttype}_{year}_{stage}_{variant}_{q_idx}"
    rows = []

    if q["type"] == "choice":
        opts = q.get("options", {})
        row = [Btn(f"{k}) {v}", callback_data=f"ans_{base}_{k}") for k, v in opts.items()]
        # по 2 кнопки в ряд
        for i in range(0, len(row), 2):
            rows.append(row[i:i+2])
    else:
        rows.append([Btn("✏️ Введите ответ в чат", callback_data=f"ans_input_{base}")])

    rows.append([Btn("💡 Как это делать?", callback_data=f"hint_{base}")])

    if q_idx < total - 1:
        rows.append([Btn("➡️ Следующий вопрос", callback_data=f"next_q_{base}")])
    else:
        rows.append([Btn("🏁 Завершить тест", callback_data=f"finish_{base}")])

    return Markup(rows)


def hint_back(base: str) -> Markup:
    return Markup([[Btn("⬅️ Вернуться к вопросу", callback_data=f"back_q_{base}")]])


# ════════════════════ СОКРАЩЁННЫЕ СБОРНИКИ ══════════════════
def short_topics_menu(subject: str, topics: list) -> Markup:
    """topics = [{"id":"q_eq","title":"Квадратные уравнения"}, ...]"""
    rows = [[Btn(t["title"], callback_data=f"short_topic_{subject}_{t['id']}")] for t in topics]
    rows.append([back(f"short_sub_{subject}")])
    return Markup(rows)


def short_page_nav(subject: str, topic_id: str, page: int, total: int) -> Markup:
    rows = []
    nav = []
    if page > 0:
        nav.append(Btn("⬅️", callback_data=f"short_pg_{subject}_{topic_id}_{page-1}"))
    nav.append(Btn(f"{page+1}/{total}", callback_data="noop"))
    if page < total - 1:
        nav.append(Btn("➡️", callback_data=f"short_pg_{subject}_{topic_id}_{page+1}"))
    rows.append(nav)
    rows.append([back(f"short_topic_{subject}_{topic_id}")])
    return Markup(rows)


# ════════════════════════ ШПАРГАЛКИ ═════════════════════════
def cheat_list(subject: str, items: list) -> Markup:
    rows = [[Btn(f"📌 {i['title']}", callback_data=f"cheat_file_{i['id']}")] for i in items]
    rows.append([back(f"cheat_sub_{subject}")])
    return Markup(rows)


# ════════════════════ РЕКЛАМА ════════════════════════════════
def ad_skip_keyboard(seconds_left: int, ad_id: int, unlocked: bool) -> Markup:
    if unlocked:
        btn = Btn("✅ Пропустить рекламу", callback_data=f"ad_skip_{ad_id}")
    else:
        btn = Btn(f"⏳ Пропустить ({seconds_left})", callback_data="ad_wait")
    return Markup([[btn]])


# ════════════════════ ПОДПИСКА ═══════════════════════════════
def subscription_keyboard(channel_url: str) -> Markup:
    return Markup([
        [Btn("📢 Подписаться на канал", url=channel_url)],
        [Btn("✅ Я подписался",         callback_data="check_sub")],
    ])


# ════════════════════ АДМИН ══════════════════════════════════
def admin_menu() -> Markup:
    return Markup([
        [Btn("📊 Статистика",         callback_data="adm_stats")],
        [Btn("📣 Управление рекламой", callback_data="adm_ads")],
        [Btn("⬅️ В главное меню",     callback_data="back_main")],
    ])


def admin_ads_menu(is_active: bool) -> Markup:
    toggle = "🔴 Выключить рекламу" if is_active else "🟢 Включить рекламу"
    return Markup([
        [Btn(toggle,                   callback_data="adm_toggle_ad")],
        [Btn("✏️ Изменить рекламу",    callback_data="adm_edit_ad")],
        [Btn("⬅️ Назад",              callback_data="adm_back")],
    ])
