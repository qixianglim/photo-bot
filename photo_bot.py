"""
Telegram Photo Forwarding Bot
- Shows area checklist on /start
- Single photos forwarded immediately
- Album photos forwarded as an album (grouped)
"""

import asyncio
import logging
from datetime import datetime, timezone, timedelta
from telegram import Update, InputMediaPhoto
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
    "3️⃣ BM Store\n"
    "4️⃣ FM Store\n"
    "5️⃣ Lift Lobby FM Cabinets _(both bottom cabinets beside glass door)_\n"
    "6️⃣ Female Toilet Store _(Drums & Keys)_\n"
    "7️⃣ Male Toilet Store _(Drums & Keys)_\n\n"
    "📸 You can send photos one by one or all at once as an album."
)

# Buffer for album photos: {media_group_id: {"photos": [], "user": user, "task": task}}
_album_buffer = {}


async def _flush_album(bot, group_id):
    """Wait briefly then send all photos in an album group together."""
    await asyncio.sleep(2)

    data = _album_buffer.pop(group_id, None)
    if not data:
        return

    photos = data["photos"]
    user = data["user"]

    sender_name = user.full_name
    if user.username:
        sender_name += f" (@{user.username})"

    now = datetime.now(TZ)
    timestamp_str = now.strftime("%d %b %Y, %I:%M %p")

    try:
        for i in range(0, len(photos), 10):
            batch = photos[i:i + 10]
            media = []
            for j, file_id in enumerate(batch):
                if j == 0 and i == 0:
                    caption = f"📸 From {sender_name}\n🕐 {timestamp_str}"
                    media.append(InputMediaPhoto(media=file_id, caption=caption))
                else:
                    media.append(InputMediaPhoto(media=file_id))

            await bot.send_media_group(
                chat_id=TARGET_GROUP_ID,
                media=media,
                message_thread_id=TARGET_TOPIC_ID,
            )
    except Exception as e:
        logging.error(f"Failed to send album: {e}")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(INSTRUCTIONS, parse_mode="Markdown")


async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    user = message.from_user
    photo = message.photo[-1]
    media_group_id = message.media_group_id

    if media_group_id:
        # Part of an album — buffer it
        if media_group_id not in _album_buffer:
            _album_buffer[media_group_id] = {"photos": [], "user": user, "task": None}

        _album_buffer[media_group_id]["photos"].append(photo.file_id)

        # Cancel and reschedule the send task
        existing_task = _album_buffer[media_group_id]["task"]
        if existing_task:
            existing_task.cancel()

        task = asyncio.create_task(_flush_album(context.bot, media_group_id))
        _album_buffer[media_group_id]["task"] = task

    else:
        # Single photo — send immediately
        sender_name = user.full_name
        if user.username:
            sender_name += f" (@{user.username})"

        now = datetime.now(TZ)
        timestamp_str = now.strftime("%d %b %Y, %I:%M %p")
        caption = f"📸 From {sender_name}\n🕐 {timestamp_str}"

        try:
            await context.bot.send_photo(
                chat_id=TARGET_GROUP_ID,
                photo=photo.file_id,
                caption=caption,
                message_thread_id=TARGET_TOPIC_ID,
            )
            await message.reply_text("✅ Your photo has been shared to the group!")
        except Exception as e:
            logging.error(f"Failed to send photo: {e}")
            await message.reply_text("❌ Something went wrong. Please try again.")


async def handle_non_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Please send a photo 📷",
        parse_mode="Markdown"
    )


def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.ChatType.PRIVATE & ~filters.PHOTO, handle_non_photo))

    print("Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
