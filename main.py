"""
main.py — точка входа бота.
Все callback_data роутятся здесь через один обработчик.
"""
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
# ВСПОМОГАТЕЛЬНАЯ ФУНКЦИЯ РОУТИНГА
# ════════════════════════════════════════════════════════════

async def _route(data: str, update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Чистый роутер — принимает data явно, без изменения объекта update."""
    q = update.callback_query

    # ── Подписка / реклама ───────────────────────────────────
    if data == "check_sub":
        await cb_check_sub(update, ctx); return
    if data.startswith("ad_skip_") or data == "ad_wait":
        await cb_ad_skip(update, ctx); return

    # ── Служебные ────────────────────────────────────────────
    if data == "back_main" or data == "main":
        await q.answer()
        await q.message.edit_text("Выбери раздел:", reply_markup=kb.main_menu())
        return
    if data == "noop":
        await q.answer(); return

    # ── Сборники ─────────────────────────────────────────────
    if data == "menu_collections":
        await cb_menu_collections(update, ctx); return
    if data.startswith("col_sub_"):
        await cb_col_subject(update, ctx, data[8:]); return
    if data.startswith("col_open_"):
        raw = data[9:]
        sep = raw.index("_")
        await cb_col_open(update, ctx, raw[:sep], raw[sep+1:]); return
    if data.startswith("col_pg_"):
        raw = data[7:]
        parts = raw.rsplit("_", 1)
        page = int(parts[1])
        sep = parts[0].index("_")
        await cb_col_page(update, ctx, parts[0][:sep], parts[0][sep+1:], page); return

    # ── Шпаргалки ────────────────────────────────────────────
    if data == "menu_cheat":
        await cb_menu_cheat(update, ctx); return
    if data.startswith("cheat_sub_"):
        await cb_cheat_subject(update, ctx, data[10:]); return
    if data.startswith("cheat_open_"):
        raw = data[11:]
        sep = raw.index("_")
        await cb_cheat_open(update, ctx, raw[:sep], raw[sep+1:]); return
    if data.startswith("cheat_pg_"):
        raw = data[9:]
        parts = raw.rsplit("_", 1)
        page = int(parts[1])
        sep = parts[0].index("_")
        await cb_cheat_page(update, ctx, parts[0][:sep], parts[0][sep+1:], page); return

    # ── Тесты ────────────────────────────────────────────────
    if data == "menu_tests":
        await cb_menu_tests(update, ctx); return
    if data.startswith("test_sub_"):
        await cb_test_subject(update, ctx, data[9:]); return
    if data.startswith("test_type_"):
        parts = data[10:].split("_", 1)
        await cb_test_type(update, ctx, parts[0], parts[1]); return
    if data.startswith("test_year_"):
        parts = data[10:].split("_", 2)
        await cb_test_year(update, ctx, parts[0], parts[1], parts[2]); return
    if data.startswith("test_stage_"):
        parts = data[11:].split("_", 3)
        await cb_test_stage(update, ctx, parts[0], parts[1], parts[2], parts[3]); return
    if data.startswith("test_var_"):
        parts = data[9:].split("_", 4)
        await cb_test_variant(update, ctx, parts[0], parts[1], parts[2], parts[3], parts[4]); return
    if data.startswith("ans_input_"):
        await cb_answer_input_prompt(update, ctx, data[10:]); return
    if data.startswith("ans_"):
        raw = data[4:]
        last = raw.rfind("_")
        answer = raw[last+1:]
        base = raw[:last]
        prev = base.rfind("_")
        q_idx_str = base[prev+1:]
        etc = base[:prev].split("_", 4)
        await cb_answer(update, ctx, etc[0], etc[1], etc[2], etc[3], etc[4], q_idx_str, answer); return
    if data.startswith("hint_"):
        await cb_hint(update, ctx, data[5:]); return
    if data.startswith("back_q_"):
        await cb_back_question(update, ctx, data[7:]); return
    if data.startswith("next_q_"):
        await cb_next_question(update, ctx, data[7:]); return
    if data.startswith("finish_"):
        await cb_finish(update, ctx, data[7:]); return

    # ── Сокращённые сборники ─────────────────────────────────
    if data == "menu_short":
        await cb_menu_short(update, ctx); return
    if data.startswith("short_sub_"):
        await cb_short_subject(update, ctx, data[10:]); return
    if data.startswith("short_topic_"):
        raw = data[12:]
        sep = raw.index("_")
        await cb_short_topic(update, ctx, raw[:sep], raw[sep+1:]); return
    if data.startswith("short_pg_"):
        raw = data[9:]
        parts = raw.rsplit("_", 1)
        sep = parts[0].index("_")
        await cb_short_page(update, ctx, parts[0][:sep], parts[0][sep+1:], int(parts[1])); return

    # ── Ссылки / Кабинет ─────────────────────────────────────
    if data == "menu_links":
        await cb_menu_links(update, ctx); return
    if data == "menu_cabinet":
        await cb_menu_cabinet(update, ctx); return

    # ── Назад (универсальный) — БЕЗ изменения update объекта ─
    if data.startswith("back_"):
        target = data[5:]
        await q.answer()
        await _route(target, update, ctx)  # ← рекурсия через _route, не через update
        return

    # ── Админ ─────────────────────────────────────────────────
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

    logger.warning("Unhandled callback_data: '%s'", data)
    await q.answer("⚙️ Неизвестная команда", show_alert=False)


# ════════════════════════════════════════════════════════════
# ТОЧКА ВХОДА ДЛЯ CALLBACK — ОБОРАЧИВАЕМ В TRY/EXCEPT
# ════════════════════════════════════════════════════════════

async def route_callback(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    data = q.data
    user = q.from_user

    try:
        await db.touch_user(user.id)
        ctx.user_data["user_id"] = user.id
        await _route(data, update, ctx)
    except Exception as e:
        logger.exception("❌ Ошибка в callback '%s': %s", data, e)
        try:
            await q.answer("❌ Что-то пошло не так. Попробуй ещё раз.", show_alert=True)
        except Exception:
            pass


# ════════════════════════════════════════════════════════════
# РОУТЕР ТЕКСТОВЫХ СООБЩЕНИЙ
# ════════════════════════════════════════════════════════════

async def route_text(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    try:
        await db.touch_user(user.id)
        ctx.user_data["user_id"] = user.id

        sess = ctx.user_data.get("test_session")
        if sess and sess.get("waiting_input") is not False and sess.get("waiting_input") is not None:
            await handle_text_answer(update, ctx)
            return

        if ctx.user_data.get("admin_state"):
            await handle_admin_input(update, ctx)
            return

    except Exception as e:
        logger.exception("❌ Ошибка в route_text: %s", e)


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
