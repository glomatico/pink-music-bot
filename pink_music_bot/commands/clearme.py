from pyrogram import filters
from pyrogram.types import Message

from ..bot import PinkMusicBot


@PinkMusicBot.on_message(
    filters.text & (filters.private | filters.group) & filters.command("clearme")
)
async def message(bot: PinkMusicBot, message: Message):
    await bot.add_free_daily_credits(message)
    lp = bot.get_lp(message)

    user = await bot.db.user.get(message.from_user.id)
    if user is None:
        await message.reply(lp("clearme_fail"))
        return
    if user.is_membership_active():
        await message.reply(lp("clearme_paid"))
        return
    if user.credits != bot.free_daily_credits:
        await message.reply(lp("clearme_free"))
        return

    await bot.db.user.delete(message.from_user.id)
    await message.reply(lp("clearme_success"))
