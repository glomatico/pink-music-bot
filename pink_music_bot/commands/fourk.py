from pyrogram import filters
from pyrogram.types import Message

from ..bot import PinkMusicBot


@PinkMusicBot.on_message(
    filters.text & (filters.private | filters.group) & filters.command("fourk")
)
async def message(bot: PinkMusicBot, message: Message):
    await bot.ensure_user_exists(message)
    lp = bot.get_lp(message)

    result = await bot.db.user.toggle_fourk_download(message.from_user.id)

    await message.reply(
        lp("fourk").format(status=lp("enabled") if result else lp("disabled"))
    )
