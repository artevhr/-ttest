"""
handlers/short_collections.py — Сокращённые сборники (пагинация по страницам).
"""
from telegram import Update
from telegram.ext import ContextTypes
import keyboards as kb
import content_loader as cl
from config import SUBJECTS


async def cb_menu_short(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.message.edit_text(
        "📖 <b>Сокращённые сборники</b>\n\nВыбери предмет:",
        reply_markup=kb.subject_menu("short"),
        parse_mode="HTML",
    )


async def cb_short_subject(update: Update, ctx: ContextTypes.DEFAULT_TYPE, subject: str):
    q = update.callback_query
    await q.answer()
    topics = cl.get_short_topics(subject)
    label = SUBJECTS.get(subject, subject)
    if not topics:
        await q.message.edit_text(
            f"📭 Для «{label}» пока нет тем.",
            reply_markup=kb.subject_menu("short"),
            parse_mode="HTML",
        )
        return
    await q.message.edit_text(
        f"📖 <b>Сокращённые сборники — {label}</b>\n\nВыбери тему:",
        reply_markup=kb.short_topics_menu(subject, topics),
        parse_mode="HTML",
    )


async def cb_short_topic(update: Update, ctx: ContextTypes.DEFAULT_TYPE,
                         subject: str, topic_id: str):
    q = update.callback_query
    await q.answer()
    await _show_page(q.message, subject, topic_id, 0)


async def cb_short_page(update: Update, ctx: ContextTypes.DEFAULT_TYPE,
                        subject: str, topic_id: str, page: int):
    q = update.callback_query
    await q.answer()
    await _show_page(q.message, subject, topic_id, page)


async def _show_page(message, subject: str, topic_id: str, page: int):
    data = cl.get_short_topic(subject, topic_id)
    if not data:
        await message.edit_text("❌ Тема не найдена.")
        return
    pages = data.get("pages", [])
    if not pages:
        await message.edit_text("📭 Страниц пока нет.")
        return

    p = pages[page]
    text = (
        f"📖 <b>{data['title']}</b>\n"
        f"<i>Страница {page + 1} из {len(pages)}: {p.get('title', '')}</i>\n\n"
        f"{p['content']}"
    )
    await message.edit_text(
        text,
        reply_markup=kb.short_page_nav(subject, topic_id, page, len(pages)),
        parse_mode="HTML",
    )
