"""
handlers/tests.py — движок прохождения тестов.

Поток:
  menu_tests → выбор предмета → выбор типа → год → этап → вариант
  → вопросы по одному → итоги

Состояние теста хранится в ctx.user_data["test_session"].
"""
from telegram import Update
from telegram.ext import ContextTypes
import keyboards as kb
import content_loader as cl
from config import SUBJECTS, TEST_TYPES


# ════ Меню тестов ════════════════════════════════════════════

async def cb_menu_tests(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.message.edit_text(
        "✏️ <b>Тесты</b>\n\nВыбери предмет:",
        reply_markup=kb.subject_menu("test"),
        parse_mode="HTML",
    )


async def cb_test_subject(update: Update, ctx: ContextTypes.DEFAULT_TYPE, subject: str):
    q = update.callback_query
    await q.answer()
    await q.message.edit_text(
        f"✏️ <b>Тесты — {SUBJECTS.get(subject, subject)}</b>\n\nВыбери тип:",
        reply_markup=kb.test_type_menu(subject),
        parse_mode="HTML",
    )


async def cb_test_type(update: Update, ctx: ContextTypes.DEFAULT_TYPE, subject: str, ttype: str):
    q = update.callback_query
    await q.answer()
    years = cl.get_test_years(subject, ttype)
    if not years:
        await q.answer("📭 Тестов пока нет.", show_alert=True)
        return
    await q.message.edit_text(
        f"✏️ <b>{TEST_TYPES.get(ttype, ttype)} — {SUBJECTS.get(subject, subject)}</b>\n\nВыбери год:",
        reply_markup=kb.test_years_menu(subject, ttype, years),
        parse_mode="HTML",
    )


async def cb_test_year(update: Update, ctx: ContextTypes.DEFAULT_TYPE,
                       subject: str, ttype: str, year: str):
    q = update.callback_query
    await q.answer()
    stages = cl.get_test_stages(subject, ttype, year)
    if not stages:
        await q.answer("📭 Этапов нет.", show_alert=True)
        return
    await q.message.edit_text(
        f"✏️ <b>{year}</b>\n\nВыбери этап:",
        reply_markup=kb.test_stages_menu(subject, ttype, year, stages),
        parse_mode="HTML",
    )


async def cb_test_stage(update: Update, ctx: ContextTypes.DEFAULT_TYPE,
                        subject: str, ttype: str, year: str, stage: str):
    q = update.callback_query
    await q.answer()
    variants = cl.get_test_variants(subject, ttype, year, stage)
    if not variants:
        await q.answer("📭 Вариантов нет.", show_alert=True)
        return
    await q.message.edit_text(
        f"✏️ Этап <b>{stage}</b>\n\nВыбери вариант:",
        reply_markup=kb.test_variants_menu(subject, ttype, year, stage, variants),
        parse_mode="HTML",
    )


async def cb_test_variant(update: Update, ctx: ContextTypes.DEFAULT_TYPE,
                          subject: str, ttype: str, year: str, stage: str, variant: str):
    q = update.callback_query
    await q.answer()
    test = cl.get_test(subject, ttype, year, stage, variant)
    if not test:
        await q.answer("❌ Тест не найден.", show_alert=True)
        return

    # Инициализируем сессию
    ctx.user_data["test_session"] = {
        "subject": subject, "ttype": ttype, "year": year,
        "stage": stage, "variant": variant,
        "test": test, "answers": {}, "q_idx": 0,
        "waiting_input": False,
    }

    await _show_question(q.message, ctx, 0)


# ════ Показ вопроса ══════════════════════════════════════════

async def _show_question(message, ctx: ContextTypes.DEFAULT_TYPE, q_idx: int):
    sess = ctx.user_data.get("test_session")
    if not sess:
        return
    test = sess["test"]
    questions = test["questions"]
    q = questions[q_idx]
    total = len(questions)

    text = (
        f"<b>Вопрос {q_idx + 1} из {total}</b>\n\n"
        f"{q['text']}"
    )
    base = f"{sess['subject']}_{sess['ttype']}_{sess['year']}_{sess['stage']}_{sess['variant']}"

    try:
        await message.edit_text(
            text,
            reply_markup=kb.question_buttons(q, q_idx, total, sess["subject"],
                                             sess["ttype"], sess["year"],
                                             sess["stage"], sess["variant"]),
            parse_mode="HTML",
        )
    except Exception:
        await message.reply_text(
            text,
            reply_markup=kb.question_buttons(q, q_idx, total, sess["subject"],
                                             sess["ttype"], sess["year"],
                                             sess["stage"], sess["variant"]),
            parse_mode="HTML",
        )


# ════ Ответы ═════════════════════════════════════════════════

async def cb_answer(update: Update, ctx: ContextTypes.DEFAULT_TYPE,
                    subject, ttype, year, stage, variant, q_idx_str, answer):
    q = update.callback_query
    await q.answer()
    sess = ctx.user_data.get("test_session")
    if not sess:
        await q.answer("❌ Сессия потеряна. Начни тест заново.", show_alert=True)
        return

    q_idx = int(q_idx_str)
    sess["answers"][q_idx] = answer

    # Переходим к следующему вопросу
    total = len(sess["test"]["questions"])
    next_idx = q_idx + 1
    if next_idx < total:
        sess["q_idx"] = next_idx
        await _show_question(q.message, ctx, next_idx)
    else:
        await _show_results(q.message, ctx)


async def cb_answer_input_prompt(update: Update, ctx: ContextTypes.DEFAULT_TYPE, base: str):
    """Просим пользователя написать ответ текстом."""
    q = update.callback_query
    await q.answer()
    sess = ctx.user_data.get("test_session")
    if not sess:
        return
    parts = base.split("_")
    q_idx = int(parts[-1])
    sess["waiting_input"] = q_idx
    await q.message.reply_text(
        f"✏️ <b>Вопрос {q_idx + 1}</b>\n\nВведи ответ в следующем сообщении:",
        parse_mode="HTML",
    )


async def handle_text_answer(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает текстовый ответ на input-вопрос."""
    sess = ctx.user_data.get("test_session")
    if not sess or sess.get("waiting_input") is False:
        return

    q_idx = sess["waiting_input"]
    sess["answers"][q_idx] = update.message.text.strip()
    sess["waiting_input"] = False

    total = len(sess["test"]["questions"])
    next_idx = q_idx + 1

    await update.message.reply_text(f"✅ Ответ принят!")

    if next_idx < total:
        sess["q_idx"] = next_idx
        # Отправляем новый вопрос отдельным сообщением
        q_data = sess["test"]["questions"][next_idx]
        text = f"<b>Вопрос {next_idx + 1} из {total}</b>\n\n{q_data['text']}"
        await update.message.reply_text(
            text,
            reply_markup=kb.question_buttons(
                q_data, next_idx, total,
                sess["subject"], sess["ttype"], sess["year"],
                sess["stage"], sess["variant"]
            ),
            parse_mode="HTML",
        )
    else:
        dummy_msg = await update.message.reply_text("⏳")
        await _show_results(dummy_msg, ctx)


# ════ Следующий вопрос (кнопка) ══════════════════════════════

async def cb_next_question(update: Update, ctx: ContextTypes.DEFAULT_TYPE, base: str):
    q = update.callback_query
    await q.answer()
    sess = ctx.user_data.get("test_session")
    if not sess:
        return
    parts = base.split("_")
    next_idx = int(parts[-1]) + 1
    sess["q_idx"] = next_idx
    await _show_question(q.message, ctx, next_idx)


# ════ Назад к вопросу (после подсказки) ══════════════════════

async def cb_back_question(update: Update, ctx: ContextTypes.DEFAULT_TYPE, base: str):
    q = update.callback_query
    await q.answer()
    sess = ctx.user_data.get("test_session")
    if not sess:
        return
    q_idx = int(base.split("_")[-1])
    await _show_question(q.message, ctx, q_idx)


# ════ Подсказка ══════════════════════════════════════════════

async def cb_hint(update: Update, ctx: ContextTypes.DEFAULT_TYPE, base: str):
    q = update.callback_query
    await q.answer()
    sess = ctx.user_data.get("test_session")
    if not sess:
        return
    q_idx    = int(base.split("_")[-1])
    question = sess["test"]["questions"][q_idx]
    expl     = question.get("explanation", question.get("hint", "Пояснение не добавлено."))
    await q.message.edit_text(
        f"💡 <b>Пояснение к заданию {q_idx + 1}</b>\n\n{expl}",
        reply_markup=kb.hint_back(base),
        parse_mode="HTML",
    )


# ════ Завершить тест ══════════════════════════════════════════

async def cb_finish(update: Update, ctx: ContextTypes.DEFAULT_TYPE, base: str):
    q = update.callback_query
    await q.answer()
    await _show_results(q.message, ctx)


async def _show_results(message, ctx: ContextTypes.DEFAULT_TYPE):
    from telegram import InlineKeyboardButton as Btn, InlineKeyboardMarkup as Markup
    import database as db_mod

    sess = ctx.user_data.get("test_session")
    if not sess:
        return

    result = cl.calc_scores(sess["test"], sess["answers"])

    lines = ["<b>📊 Результаты теста</b>\n"]
    for d in result["details"]:
        icon = "✅" if d["is_correct"] else "❌"
        user_ans = d["user_ans"] if d["user_ans"] is not None else "—"
        correct  = d["correct"]
        if isinstance(correct, list):
            correct = correct[0]
        line = f"{icon} <b>Задание {d['q_idx']}</b>: твой ответ — <i>{user_ans}</i>"
        if not d["is_correct"]:
            line += f"\n    ↳ Правильно: <i>{correct}</i>"
            if d.get("explanation"):
                line += f"\n    💡 {d['explanation']}"
        lines.append(line)

    lines.append(
        f"\n📌 <b>Первичный балл:</b> {result['primary']} / {result['max_primary']}\n"
        f"🎯 <b>Тестовый балл:</b> {result['test_score']}"
    )

    # Сохраняем в БД
    user_id = ctx.user_data.get("user_id", 0)
    await db_mod.save_result(
        user_id,
        sess["subject"], sess["ttype"], sess["year"],
        sess["stage"], sess["variant"],
        result["primary"], result["test_score"], result["max_primary"],
    )

    ctx.user_data.pop("test_session", None)

    await message.edit_text(
        "\n".join(lines),
        reply_markup=Markup([[Btn("🏠 В главное меню", callback_data="back_main")]]),
        parse_mode="HTML",
    )
