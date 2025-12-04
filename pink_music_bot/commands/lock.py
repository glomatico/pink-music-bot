import logging
from pathlib import Path

from pyrogram import filters
from pyrogram.types import Message

from ..bot import PinkMusicBot

logger = logging.getLogger(__name__)


@PinkMusicBot.on_message(
    filters.text & (filters.private | filters.group) & filters.command("lock")
)
async def message(bot: PinkMusicBot, message: Message):
    if not bot.is_admin(message):
        return
    lp = bot.get_lp(message)

    if Path("lock").exists():
        Path("lock").unlink()
        await message.reply(lp("lock").format(status=lp("disabled")))
    else:
        Path("lock").touch()
        await message.reply(lp("lock").format(status=lp("enabled")))
