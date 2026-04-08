"""
main.py — точка входа бота.

Все callback_data роутятся здесь через один обработчик.
"""
import asyncio
import logging
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes,
)

from config import BOT_TOKEN
import database as db
from handlers.start import cmd_start, cb_check_sub, cb_ad_skip
from handlers.collections import (
    cb_menu_collections, cb_col_subject, cb_col_open, cb_col_page,
    cb_menu_cheat, cb_cheat_subject, cb_cheat_open, cb_cheat_page,
)
from handlers.tests import (
    cb_menu_tests, cb_test_subject, cb_test_type,
    cb_test_year, cb_test_stage, cb_test_variant,
    cb_answer, cb_hint, cb_finish, cb_next_question,
    cb_back_question, cb_answer_input_prompt, handle_text_answer,
)
from handlers.short_collections import (
    cb_menu_short, cb_short_subject, cb_short_topic, cb_short_page,
)
from handlers.links import cb_menu_links
from handlers.cabinet import cb_menu_cabinet
from handlers.admin import (
    cmd_admin, cb_adm_stats, cb_adm_ads, cb_adm_toggle_ad,
    cb_adm_edit_ad, handle_admin_input, cb_adm_back,
)
import keyboards as kb

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ════════════════════════════════════════════════════════════
# ГЛАВНЫЙ РОУТЕР CALLBACK
# ════════════════════════════════════════════════════════════

async def route_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    data = q.data
    user = q.from_user
    await db.touch_user(user.id)
    ctx.user_data["user_id"] = user.id

    # ── Подписка / реклама ───────────────────────────────
    if data == "check_sub":
        await cb_check_sub(update, ctx); return
    if data.startswith("ad_skip_") or data == "ad_wait":
        await cb_ad_skip(update, ctx); return

    # ── Главное меню ─────────────────────────────────────
    if data == "back_main":
        await q.answer()
        await q.message.edit_text("Выбери раздел:", reply_markup=kb.main_menu()); return
    if data == "noop":
        await q.answer(); return

    # ── Сборники ─────────────────────────────────────────
    if data == "menu_collections":
        await cb_menu_collections(update, ctx); return
    if data.startswith("col_sub_"):
        await cb_col_subject(update, ctx, data[8:]); return
    if data.startswith("col_open_"):
        # col_open_math_math_col_001  → subject=math, id=math_col_001
        raw = data[9:]
        sep = raw.index("_")
        await cb_col_open(update, ctx, raw[:sep], raw[sep+1:]); return
    if data.startswith("col_pg_"):
        # col_pg_math_math_col_001_2
        raw   = data[7:]
        parts = raw.rsplit("_", 1)
        page  = int(parts[1])
        sep   = parts[0].index("_")
        await cb_col_page(update, ctx, parts[0][:sep], parts[0][sep+1:], page); return

    # ── Шпаргалки ────────────────────────────────────────
    if data == "menu_cheat":
        await cb_menu_cheat(update, ctx); return
    if data.startswith("cheat_sub_"):
        await cb_cheat_subject(update, ctx, data[10:]); return
    if data.startswith("cheat_open_"):
        raw = data[11:]
        sep = raw.index("_")
        await cb_cheat_open(update, ctx, raw[:sep], raw[sep+1:]); return
    if data.startswith("cheat_pg_"):
        # cheat_pg_math_math_cheat_001_1
        raw   = data[9:]
        parts = raw.rsplit("_", 1)
        page  = int(parts[1])
        sep   = parts[0].index("_")
        await cb_cheat_page(update, ctx, parts[0][:sep], parts[0][sep+1:], page); return

    # ── Тесты ────────────────────────────────────────────
    if data == "menu_tests":
        await cb_menu_tests(update, ctx); return
    if data.startswith("test_sub_"):
        await cb_test_subject(update, ctx, data[9:]); return

    if data.startswith("test_type_"):
        # test_type_math_drt
        parts = data[10:].split("_", 1)
        await cb_test_type(update, ctx, parts[0], parts[1]); return

    if data.startswith("test_year_"):
        # test_year_math_drt_2025-2026
        parts = data[10:].split("_", 2)
        await cb_test_year(update, ctx, parts[0], parts[1], parts[2]); return

    if data.startswith("test_stage_"):
        # test_stage_math_drt_2025-2026_I
        parts = data[11:].split("_", 3)
        await cb_test_stage(update, ctx, parts[0], parts[1], parts[2], parts[3]); return

    if data.startswith("test_var_"):
        # test_var_math_drt_2025-2026_I_1
        parts = data[9:].split("_", 4)
        await cb_test_variant(update, ctx, parts[0], parts[1], parts[2], parts[3], parts[4]); return

    if data.startswith("ans_input_"):
        await cb_answer_input_prompt(update, ctx, data[10:]); return

    if data.startswith("ans_"):
        # ans_math_drt_2025-2026_I_1_0_B
        raw = data[4:]
        # последний _ разделяет base и ответ
        last = raw.rfind("_")
        base = raw[:last]
        answer = raw[last+1:]
        # предпоследний _ разделяет base и q_idx
        prev = base.rfind("_")
        q_idx_str = base[prev+1:]
        subject_ttype_etc = base[:prev].split("_", 4)  # subject ttype year stage variant
        await cb_answer(update, ctx,
                        subject_ttype_etc[0], subject_ttype_etc[1],
                        subject_ttype_etc[2], subject_ttype_etc[3],
                        subject_ttype_etc[4],
                        q_idx_str, answer); return

    if data.startswith("hint_"):
        await cb_hint(update, ctx, data[5:]); return

    if data.startswith("back_q_"):
        await cb_back_question(update, ctx, data[7:]); return

    if data.startswith("next_q_"):
        await cb_next_question(update, ctx, data[7:]); return

    if data.startswith("finish_"):
        await cb_finish(update, ctx, data[7:]); return

    # ── Сокращённые сборники ─────────────────────────────
    if data == "menu_short":
        await cb_menu_short(update, ctx); return
    if data.startswith("short_sub_"):
        await cb_short_subject(update, ctx, data[10:]); return
    if data.startswith("short_topic_"):
        # short_topic_math_quadratic
        raw = data[12:]
        sep = raw.index("_")
        await cb_short_topic(update, ctx, raw[:sep], raw[sep+1:]); return
    if data.startswith("short_pg_"):
        # short_pg_math_quadratic_0
        raw = data[9:]
        parts = raw.rsplit("_", 1)
        sep = parts[0].index("_")
        subject = parts[0][:sep]
        topic_id = parts[0][sep+1:]
        await cb_short_page(update, ctx, subject, topic_id, int(parts[1])); return

    # ── Ссылки / Кабинет ─────────────────────────────────
    if data == "menu_links":
        await cb_menu_links(update, ctx); return
    if data == "menu_cabinet":
        await cb_menu_cabinet(update, ctx); return

    # ── Назад (универсальный) ────────────────────────────
    if data.startswith("back_"):
        target = data[5:]
        if target == "main":
            await q.answer()
            await q.message.edit_text("Выбери раздел:", reply_markup=kb.main_menu()); return
        # back_col_sub_math → col_sub_math
        await q.answer()
        ctx.bot_data["_back_data"] = target
        update.callback_query.data = target
        await route_callback(update, ctx); return

    # ── Админ ─────────────────────────────────────────────
    if data == "adm_stats":
        await cb_adm_stats(update, ctx); return
    if data == "adm_ads":
        await cb_adm_ads(update, ctx); return
    if data == "adm_toggle_ad":
        await cb_adm_toggle_ad(update, ctx); return
    if data == "adm_edit_ad":
        await cb_adm_edit_ad(update, ctx); return
    if data == "adm_back":
        await cb_adm_back(update, ctx); return

    logger.warning("Unhandled callback: %s", data)
    await q.answer()


# ════════════════════════════════════════════════════════════
# РОУТЕР ТЕКСТОВЫХ СООБЩЕНИЙ
# ════════════════════════════════════════════════════════════

async def route_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await db.touch_user(user.id)
    ctx.user_data["user_id"] = user.id

    # Если ждём текстовый ответ на вопрос теста
    sess = ctx.user_data.get("test_session")
    if sess and sess.get("waiting_input") is not False and sess.get("waiting_input") is not None:
        await handle_text_answer(update, ctx)
        return

    # Если ждём ввод рекламы от админа
    from handlers.admin import handle_admin_input
    if ctx.user_data.get("admin_state"):
        await handle_admin_input(update, ctx)
        return


# ════════════════════════════════════════════════════════════
# ЗАПУСК
# ════════════════════════════════════════════════════════════

async def post_init(app: Application):
    await db.init_db()
    logger.info("БД инициализирована ✅")


def main():
    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("admin", cmd_admin))
    app.add_handler(CallbackQueryHandler(route_callback))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, route_text))

    logger.info("Бот запущен 🚀")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
