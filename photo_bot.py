"""
Telegram Photo Forwarding Bot
- Shows area checklist on /start or any text message
- Forwards photos to group topic immediately
- Sends ONE confirmation per album or single photo
"""

import logging
from datetime import datetime, timezone, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, CommandHandler, filters, ContextTypes

# ── CONFIG ────────────────────────────────────────────────────────────────────
BOT_TOKEN = "8933424558:AAFjKsR6clDquSvw6BxHuU_A68PgJMwp7Zc"
TARGET_GROUP_ID = -1003900839389
TARGET_TOPIC_ID = 2
TIMEZONE_OFFSET = 8                        # UTC+8 (Singapore time)
# ─────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

TZ = timezone(timedelta(hours=TIMEZONE_OFFSET))

INSTRUCTIONS = (
    "👋 *Welcome to the BM Consumables Stock Count Bot!*\n\n"
    "Please take photos of the following areas and send them here:\n\n"
    "1️⃣ BM Riser\n"
    "2️⃣ Atrium Electrical Riser\n"
    "3️⃣ Paint Riser\n"
    "4️⃣ BM Store\n"
    "5️⃣ FM Store\n"
    "6️⃣ Lift Lobby FM Cabinets _(both bottom cabinets beside glass door)_\n"
    "7️⃣ Female Toilet Store _(Drums & Keys)_\n"
    "8️⃣ Male Toilet Store _(Drums & Keys)_\n\n"
    "📸 You can send photos one by one or all at once as an album."
)

# Track which album groups we've already confirmed, to avoid duplicate replies
_confirmed_groups = set()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(INSTRUCTIONS, parse_mode="Markdown")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    user = message.from_user
    photo = message.photo[-1]
    media_group_id = message.media_group_id

    sender_name = user.full_name
    if user.username:
        sender_name += f" (@{user.username})"

    now = datetime.now(TZ)
    timestamp_str = now.strftime("%d %b %Y, %I:%M %p")

    # Only add caption to single photos or the first photo of an album
    is_first_of_album = media_group_id and media_group_id not in _confirmed_groups
    add_caption = (not media_group_id) or is_first_of_album
    user_caption = message.caption or ""
    if add_caption:
        caption = f"📸 From {sender_name}\n🕐 {timestamp_str}"
        if user_caption:
            caption += f"\n\n{user_caption}"
    else:
        caption = user_caption if user_caption else None

    try:
        await context.bot.send_photo(
            chat_id=TARGET_GROUP_ID,
            photo=photo.file_id,
            caption=caption,
            message_thread_id=TARGET_TOPIC_ID,
        )

        # Send confirmation — once per album, always for single photos
        if media_group_id:
            if media_group_id not in _confirmed_groups:
                _confirmed_groups.add(media_group_id)
                await message.reply_text("✅ Your photos have been shared to the group!")
        else:
            await message.reply_text("✅ Your photo has been shared to the group!")

    except Exception as e:
        logging.error(f"Failed to forward photo: {e}")
        await message.reply_text("❌ Something went wrong. Please try again.")


async def handle_non_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(INSTRUCTIONS, parse_mode="Markdown")


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & ~filters.PHOTO, handle_non_photo))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
