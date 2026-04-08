"""
handlers/collections.py — Сборники и Шпаргалки.
Всё отображается текстом с пагинацией по страницам — никаких файлов.
"""
from telegram import Update, InlineKeyboardButton as Btn, InlineKeyboardMarkup as Markup
from telegram.ext import ContextTypes
import keyboards as kb
import content_loader as cl
from config import SUBJECTS


# ══════════════════════════════════════════════════
# ОБЩИЙ ПЕЙДЖИНГ (используется и для сборников, и для шпор)
# ══════════════════════════════════════════════════

def _page_keyboard(section: str, subject: str, item_id: str, page: int, total: int,
                   back_cb: str) -> Markup:
    nav = []
    if page > 0:
        nav.append(Btn("⬅️", callback_data=f"{section}_pg_{subject}_{item_id}_{page-1}"))
    nav.append(Btn(f"{page+1}/{total}", callback_data="noop"))
    if page < total - 1:
        nav.append(Btn("➡️", callback_data=f"{section}_pg_{subject}_{item_id}_{page+1}"))
    rows = []
    if nav:
        rows.append(nav)
    rows.append([Btn("⬅️ К списку", callback_data=back_cb)])
    return Markup(rows)


async def _show_page(message, section: str, subject: str, item_id: str,
                     page: int, data: dict, back_cb: str, edit: bool = True):
    pages = data.get("pages", [])
    if not pages:
        text = f"<b>{data['title']}</b>\n\n📭 Страниц пока нет."
        kb_  = Markup([[Btn("⬅️ Назад", callback_data=back_cb)]])
    else:
        p    = pages[page]
        text = (
            f"<b>{data['title']}</b>\n"
            f"<i>Стр. {page+1}/{len(pages)}"
            + (f" — {p['title']}" if p.get("title") else "") +
            "</i>\n\n"
            f"{p['content']}"
        )
        kb_  = _page_keyboard(section, subject, item_id, page, len(pages), back_cb)
    if edit:
        await message.edit_text(text, reply_markup=kb_, parse_mode="HTML")
    else:
        await message.reply_text(text, reply_markup=kb_, parse_mode="HTML")


# ══════════════════════════════════════════════════
# СБОРНИКИ
# ══════════════════════════════════════════════════

async def cb_menu_collections(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.message.edit_text(
        "📚 <b>Сборники</b>\n\nВыбери предмет:",
        reply_markup=kb.subject_menu("col"), parse_mode="HTML"
    )


async def cb_col_subject(update: Update, ctx: ContextTypes.DEFAULT_TYPE, subject: str):
    q = update.callback_query
    await q.answer()
    items = cl.get_collections(subject)
    label = SUBJECTS.get(subject, subject)
    if not items:
        await q.message.edit_text(
            f"📭 Для «{label}» сборников пока нет.",
            reply_markup=kb.subject_menu("col"), parse_mode="HTML"
        )
        return
    rows = [[Btn(f"📄 {i['title']}", callback_data=f"col_open_{subject}_{i['id']}")] for i in items]
    rows.append([Btn("⬅️ Назад", callback_data="back_main")])
    await q.message.edit_text(
        f"📚 <b>Сборники — {label}</b>\n\nВыбери сборник:",
        reply_markup=Markup(rows), parse_mode="HTML"
    )


async def cb_col_open(update: Update, ctx: ContextTypes.DEFAULT_TYPE, subject: str, col_id: str):
    q = update.callback_query
    await q.answer()
    data = cl.get_collection(subject, col_id)
    if not data:
        await q.answer("❌ Сборник не найден.", show_alert=True)
        return
    await _show_page(q.message, "col", subject, col_id, 0, data,
                     back_cb=f"col_sub_{subject}")


async def cb_col_page(update: Update, ctx: ContextTypes.DEFAULT_TYPE,
                      subject: str, col_id: str, page: int):
    q = update.callback_query
    await q.answer()
    data = cl.get_collection(subject, col_id)
    if not data:
        await q.answer("❌ Сборник не найден.", show_alert=True)
        return
    await _show_page(q.message, "col", subject, col_id, page, data,
                     back_cb=f"col_sub_{subject}")


# ══════════════════════════════════════════════════
# ШПАРГАЛКИ
# ══════════════════════════════════════════════════

async def cb_menu_cheat(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.message.edit_text(
        "📋 <b>Шпаргалки</b>\n\nВыбери предмет:",
        reply_markup=kb.subject_menu("cheat"), parse_mode="HTML"
    )


async def cb_cheat_subject(update: Update, ctx: ContextTypes.DEFAULT_TYPE, subject: str):
    q = update.callback_query
    await q.answer()
    items = cl.get_cheatsheets(subject)
    label = SUBJECTS.get(subject, subject)
    if not items:
        await q.message.edit_text(
            f"📭 Для «{label}» шпаргалок пока нет.",
            reply_markup=kb.subject_menu("cheat"), parse_mode="HTML"
        )
        return
    rows = [[Btn(f"📌 {i['title']}", callback_data=f"cheat_open_{subject}_{i['id']}")] for i in items]
    rows.append([Btn("⬅️ Назад", callback_data="back_main")])
    await q.message.edit_text(
        f"📋 <b>Шпаргалки — {label}</b>\n\nВыбери:",
        reply_markup=Markup(rows), parse_mode="HTML"
    )


async def cb_cheat_open(update: Update, ctx: ContextTypes.DEFAULT_TYPE, subject: str, cheat_id: str):
    q = update.callback_query
    await q.answer()
    data = cl.get_cheatsheet(subject, cheat_id)
    if not data:
        await q.answer("❌ Шпаргалка не найдена.", show_alert=True)
        return
    await _show_page(q.message, "cheat", subject, cheat_id, 0, data,
                     back_cb=f"cheat_sub_{subject}")


async def cb_cheat_page(update: Update, ctx: ContextTypes.DEFAULT_TYPE,
                        subject: str, cheat_id: str, page: int):
    q = update.callback_query
    await q.answer()
    data = cl.get_cheatsheet(subject, cheat_id)
    if not data:
        await q.answer("❌ Не найдено.", show_alert=True)
        return
    await _show_page(q.message, "cheat", subject, cheat_id, page, data,
                     back_cb=f"cheat_sub_{subject}")
