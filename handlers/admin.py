"""
handlers/admin.py — админ-панель.

Команда /admin — только для пользователей из ADMIN_IDS.
"""
from telegram import Update, InlineKeyboardButton as Btn, InlineKeyboardMarkup as Markup
from telegram.ext import ContextTypes
import database as db_mod
import keyboards as kb
import content_loader as cl
from config import ADMIN_IDS, SUBJECTS, TEST_TYPES
import os


def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


async def cmd_admin(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        await update.message.reply_text("⛔ Нет доступа.")
        return
    await update.message.reply_text(
        "🛠 <b>Админ-панель</b>",
        reply_markup=kb.admin_menu(),
        parse_mode="HTML",
    )


# ════ Статистика ══════════════════════════════════════════════

async def cb_adm_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    q = update.callback_query
    await q.answer()

    stats = await db_mod.get_stats()

    # Считаем сборники, тесты, шпоры
    total_cols = sum(len(cl.get_collections(s)) for s in SUBJECTS)
    total_cheat = sum(len(cl.get_cheatsheets(s)) for s in SUBJECTS)
    total_tests = 0
    for s in SUBJECTS:
        for t in TEST_TYPES:
            for y in cl.get_test_years(s, t):
                for st in cl.get_test_stages(s, t, y):
                    total_tests += len(cl.get_test_variants(s, t, y, st))

    text = (
        "📊 <b>Статистика бота</b>\n\n"
        f"👥 Всего пользователей: <b>{stats['total_users']}</b>\n"
        f"🟢 Активных сегодня: <b>{stats['active_today']}</b>\n"
        f"✅ Тестов пройдено: <b>{stats['tests_done']}</b>\n\n"
        f"📚 Сборников: <b>{total_cols}</b>\n"
        f"✏️ Тестов в базе: <b>{total_tests}</b>\n"
        f"📌 Шпаргалок: <b>{total_cheat}</b>"
    )
    await q.message.edit_text(
        text,
        reply_markup=Markup([[Btn("⬅️ Назад", callback_data="adm_back")]]),
        parse_mode="HTML",
    )


# ════ Реклама ═════════════════════════════════════════════════

async def cb_adm_ads(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    q = update.callback_query
    await q.answer()
    ad = await db_mod.get_active_ad()
    is_active = bool(ad and ad["is_active"])

    ad_info = ""
    if ad:
        ad_info = (
            f"\n\n<b>Текущая реклама:</b>\n"
            f"📢 Канал: {ad.get('channel_name', '—')}\n"
            f"🔗 Ссылка: {ad.get('channel_url', '—')}\n"
            f"📝 Текст: {(ad.get('ad_text') or '')[:80]}...\n"
            f"⏱ Отсчёт: {ad.get('countdown', 5)} сек."
        )
    else:
        ad_info = "\n\n<i>Реклама не настроена.</i>"

    status = "🟢 Реклама включена" if is_active else "🔴 Реклама выключена"
    await q.message.edit_text(
        f"📣 <b>Управление рекламой</b>\n{status}{ad_info}",
        reply_markup=kb.admin_ads_menu(is_active),
        parse_mode="HTML",
    )


async def cb_adm_toggle_ad(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    q = update.callback_query
    await q.answer()
    ad = await db_mod.get_active_ad()
    new_state = not bool(ad and ad["is_active"])
    await db_mod.set_ad_active(new_state)
    status = "включена ✅" if new_state else "выключена ❌"
    await q.answer(f"Реклама {status}", show_alert=True)
    await cb_adm_ads(update, ctx)


async def cb_adm_edit_ad(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    q = update.callback_query
    await q.answer()
    ctx.user_data["admin_state"] = "waiting_ad"
    await q.message.edit_text(
        "📣 <b>Настройка рекламы</b>\n\n"
        "Отправь данные в формате (каждое на новой строке):\n\n"
        "<code>URL фото (или - если без фото)\n"
        "URL канала (https://t.me/...)\n"
        "Название канала\n"
        "Текст рекламы\n"
        "Секунды до пропуска (число, например 5)</code>",
        reply_markup=Markup([[Btn("❌ Отмена", callback_data="adm_ads")]]),
        parse_mode="HTML",
    )


async def handle_admin_input(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает текстовый ввод от администратора."""
    if not is_admin(update.effective_user.id):
        return
    state = ctx.user_data.get("admin_state")
    if state != "waiting_ad":
        return

    lines = update.message.text.strip().split("\n")
    if len(lines) < 5:
        await update.message.reply_text(
            "❌ Нужно 5 строк. Попробуй снова или нажми /admin."
        )
        return

    photo_url  = lines[0].strip() if lines[0].strip() != "-" else None
    channel_url = lines[1].strip()
    channel_name = lines[2].strip()
    ad_text    = lines[3].strip()
    try:
        countdown = int(lines[4].strip())
    except ValueError:
        countdown = 5

    await db_mod.upsert_ad(photo_url, channel_url, channel_name, ad_text, countdown)
    ctx.user_data.pop("admin_state", None)
    await update.message.reply_text(
        "✅ Реклама сохранена и включена!",
        reply_markup=kb.admin_menu(),
    )


async def cb_adm_back(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not is_admin(update.effective_user.id):
        return
    q = update.callback_query
    await q.answer()
    await q.message.edit_text(
        "🛠 <b>Админ-панель</b>",
        reply_markup=kb.admin_menu(),
        parse_mode="HTML",
    )
