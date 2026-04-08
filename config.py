import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN        = os.getenv("BOT_TOKEN", "")
CHANNEL_USERNAME = os.getenv("CHANNEL_USERNAME", "@your_channel")   # с @
ADMIN_IDS        = [int(x) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip()]
DB_PATH          = os.getenv("DB_PATH", "bot.db")
CONTENT_DIR      = "content"

SUBJECTS = {
    "russian": "🇷🇺 Русский язык",
    "math":    "📐 Математика",
    "english": "🇬🇧 Английский язык",
}

TEST_TYPES = {
    "drt":        "📝 ДРТ",
    "rt":         "📋 РТ",
    "ct":         "📄 ЦТ",
    "additional": "➕ Дополнительные",
}
