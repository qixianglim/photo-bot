"""
Telegram Photo Forwarding Bot
- Users DM the bot with a photo
- Bot forwards it to a target group chat with timestamp, date, and sender info
"""

import logging
from datetime import datetime, timezone, timedelta
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, ContextTypes

# ── CONFIG ────────────────────────────────────────────────────────────────────
BOT_TOKEN = "8933424558:AAFjKsR6clDquSvw6BxHuU_A68PgJMwp7Zc"
TARGET_GROUP_ID = -1003900839389
TARGET_TOPIC_ID = 2
TIMEZONE_OFFSET = 8                        # UTC+8 (Singapore time).
# ─────────────────────────────────────────────────────────────────────────────

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

TZ = timezone(timedelta(hours=TIMEZONE_OFFSET))


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    user = message.from_user

    # Build sender display name
    sender_name = user.full_name
    if user.username:
        sender_name += f" (@{user.username})"

    # Timestamp in local timezone
    now = datetime.now(TZ)
    timestamp_str = now.strftime("%d %b %Y, %I:%M %p")  # e.g. 10 Jun 2026, 03:45 PM

    # Caption to attach
    original_caption = message.caption or ""
    caption = (
        f"📸 Photo from {sender_name}\n"
        f"🕐 {timestamp_str}\n"
    )
    if original_caption:
        caption += f"\n{original_caption}"

    # Get the highest-resolution photo
    photo = message.photo[-1]

    try:
        await context.bot.send_photo(
            chat_id=TARGET_GROUP_ID,
            photo=photo.file_id,
            caption=caption,
            message_thread_id=TARGET_TOPIC_ID,
        )
        # Acknowledge back to sender
        await message.reply_text("✅ Your photo has been shared to the group!")
    except Exception as e:
        logging.error(f"Failed to forward photo: {e}")
        await message.reply_text("❌ Something went wrong. Please try again.")


async def handle_non_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Please send a photo 📷")


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & ~filters.PHOTO, handle_non_photo))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
