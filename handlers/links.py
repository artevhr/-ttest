"""
handlers/links.py — Полезные ссылки.

КАК ДОБАВИТЬ ССЫЛКУ:
  Просто добавь ещё один словарь в список LINKS ниже.
  {"title": "Название", "url": "https://..."}
"""
from telegram import Update, InlineKeyboardButton as Btn, InlineKeyboardMarkup as Markup
from telegram.ext import ContextTypes


# ════ РЕДАКТИРУЙ ЗДЕСЬ ════════════════════════════════════════
LINKS = [
    # {"title": "Сайт ЦТ Беларуси",          "url": "https://ctest.by"},
    # {"title": "Решу ЦТ — математика",       "url": "https://math-ct.sdamgia.ru"},
    # {"title": "Английский онлайн",          "url": "https://puzzle-english.com"},
    # Добавляй сюда:
]
# ═════════════════════════════════════════════════════════════


async def cb_menu_links(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if not LINKS:
        await q.message.edit_text(
            "🔗 <b>Полезные ссылки</b>\n\n📭 Ссылок пока нет.",
            reply_markup=Markup([[Btn("⬅️ Назад", callback_data="back_main")]]),
            parse_mode="HTML",
        )
        return

    rows = [[Btn(f"🔗 {link['title']}", url=link["url"])] for link in LINKS]
    rows.append([Btn("⬅️ Назад", callback_data="back_main")])

    await q.message.edit_text(
        "🔗 <b>Полезные ссылки</b>\n\nВыбери ресурс:",
        reply_markup=Markup(rows),
        parse_mode="HTML",
    )
