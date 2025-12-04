import datetime

from pyrogram import filters
from pyrogram.types import Message

from ..bot import PinkMusicBot


@PinkMusicBot.on_message(filters.text & filters.command("ping"))
async def message(bot: PinkMusicBot, message: Message):
    time_diff = datetime.datetime.now() - message.date
    ping_message = [
        f"🏓 Pong! Response time: {time_diff.total_seconds():.3f}s.",
        f"Chat ID: <code>{message.chat.id}</code>",
    ]

    if hasattr(message.from_user, "id"):
        ping_message.append(f"User ID: <code>{message.from_user.id}</code>")

    if message.message_thread_id:
        ping_message.append(f"Thread ID: <code>{message.message_thread_id}</code>")

    await message.reply("\n".join(ping_message))
