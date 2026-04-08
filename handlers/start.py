"""
handlers/start.py
Запуск бота, проверка подписки на канал, показ рекламы.
"""
import asyncio
import logging
from telegram import Update
from telegram.ext import ContextTypes

import database as db
import keyboards as kb
from config import CHANNEL_USERNAME

logger = logging.getLogger(__name__)


# ── Проверка подписки ────────────────────────────────────────
async def is_subscribed(bot, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(CHANNEL_USERNAME, user_id)
        return member.status in ("member", "administrator", "creator")
    except Exception:
        return False


async def require_subscription(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Возвращает True если пользователь подписан.
    Иначе шлёт сообщение с кнопкой и возвращает False.
    """
    user_id = update.effective_user.id
    if await is_subscribed(ctx.bot, user_id):
        return True

    text = (
        "📢 Чтобы пользоваться ботом, подпишись на канал!\n\n"
        "После подписки нажми <b>✅ Я подписался</b>."
    )
    channel_url = f"https://t.me/{CHANNEL_USERNAME.lstrip('@')}"
    keyboard = kb.subscription_keyboard(channel_url)

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.edit_text(text, reply_markup=keyboard, parse_mode="HTML")
    else:
        await update.message.reply_text(text, reply_markup=keyboard, parse_mode="HTML")
    return False


# ── Реклама с обратным отсчётом ─────────────────────────────
async def show_ad(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> bool:
    """
    Показывает рекламу с обратным отсчётом.
    Возвращает True когда реклама показана (или её нет).
    Возвращает False чтобы заблокировать дальнейший ответ на этот апдейт
    (бот сам продолжит после показа).
    """
    ad = await db.get_active_ad()
    if not ad:
        return True  # рекламы нет — пускаем дальше

    user_id = update.effective_user.id
    # Если уже видел рекламу в этой сессии — пускаем
    seen = ctx.user_data.get("ad_seen_id")
    if seen == ad["id"]:
        return True

    countdown = ad.get("countdown", 5)
    caption = (
        f"{ad['ad_text']}\n\n"
        f"<i>Это — реклама, которая помогает жить боту 🙏</i>"
    )

    chat_id = update.effective_chat.id

    if ad.get("photo_url"):
        msg = await ctx.bot.send_photo(
            chat_id=chat_id,
            photo=ad["photo_url"],
            caption=caption,
            parse_mode="HTML",
            reply_markup=kb.ad_skip_keyboard(countdown, ad["id"], False),
        )
    else:
        msg = await ctx.bot.send_message(
            chat_id=chat_id,
            text=caption,
            parse_mode="HTML",
            reply_markup=kb.ad_skip_keyboard(countdown, ad["id"], False),
        )

    # Обратный отсчёт: редактируем клавиатуру каждую секунду
    for sec in range(countdown - 1, -1, -1):
        await asyncio.sleep(1)
        try:
            if ad.get("photo_url"):
                await ctx.bot.edit_message_caption(
                    chat_id=chat_id,
                    message_id=msg.message_id,
                    caption=caption,
                    parse_mode="HTML",
                    reply_markup=kb.ad_skip_keyboard(sec, ad["id"], sec == 0),
                )
            else:
                await ctx.bot.edit_message_reply_markup(
                    chat_id=chat_id,
                    message_id=msg.message_id,
                    reply_markup=kb.ad_skip_keyboard(sec, ad["id"], sec == 0),
                )
        except Exception:
            pass

    # Помечаем что реклама показана в этой сессии
    ctx.user_data["ad_seen_id"] = ad["id"]
    return True  # теперь можно продолжать


# ── /start ──────────────────────────────────────────────────
async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await db.upsert_user(user.id, user.username or "", user.first_name or "")

    if not await require_subscription(update, ctx):
        return

    await show_ad(update, ctx)

    text = (
        f"👋 Привет, <b>{user.first_name}</b>!\n\n"
        "Я — помощник по РТ. Выбери раздел:"
    )
    await update.message.reply_text(text, reply_markup=kb.main_menu(), parse_mode="HTML")


# ── Callback: проверка подписки (кнопка «Я подписался») ─────
async def cb_check_sub(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if not await is_subscribed(ctx.bot, q.from_user.id):
        await q.answer("❌ Ты ещё не подписан! Подпишись и попробуй снова.", show_alert=True)
        return

    await q.message.delete()
    text = (
        f"✅ Отлично, <b>{q.from_user.first_name}</b>! Добро пожаловать.\n\n"
        "Выбери раздел:"
    )
    await ctx.bot.send_message(q.message.chat_id, text, reply_markup=kb.main_menu(), parse_mode="HTML")


# ── Callback: пропустить рекламу ────────────────────────────
async def cb_ad_skip(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    if q.data == "ad_wait":
        await q.answer("⏳ Подожди, пока реклама не закончится!", show_alert=True)
        return

    await q.answer("✅ Реклама закрыта")
    try:
        await q.message.delete()
    except Exception:
        pass

    # Показываем главное меню
    await ctx.bot.send_message(
        q.message.chat_id,
        "Выбери раздел:",
        reply_markup=kb.main_menu(),
    )
