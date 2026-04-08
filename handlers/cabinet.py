from telegram import Update, InlineKeyboardButton as Btn, InlineKeyboardMarkup as Markup
from telegram.ext import ContextTypes


async def cb_menu_cabinet(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.message.edit_text(
        "👤 <b>Личный кабинет</b>\n\n🔧 <i>В разработке...</i>",
        reply_markup=Markup([[Btn("⬅️ Назад", callback_data="back_main")]]),
        parse_mode="HTML",
    )
