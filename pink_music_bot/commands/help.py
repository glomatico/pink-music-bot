from pyrogram import filters
from pyrogram.types import Message

from ..bot import PinkMusicBot


@PinkMusicBot.on_message(
    filters.text & (filters.private | filters.group) & filters.command("help")
)
async def message(bot: PinkMusicBot, message: Message):
    lp = bot.get_lp(message)

    await message.reply(
        lp("help").format(
            bot_username=(await bot.get_me()).username,
        )
    )
