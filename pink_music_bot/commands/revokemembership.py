import logging

from pyrogram import filters
from pyrogram.types import Message

from ..bot import PinkMusicBot

logger = logging.getLogger(__name__)


@PinkMusicBot.on_message(
    filters.text
    & (filters.private | filters.group)
    & filters.command("revokemembership")
)
async def message(bot: PinkMusicBot, message: Message):
    if not bot.is_admin(message):
        return
    lp = bot.get_lp(message)

    if len(message.command) < 2:
        await message.reply(lp("revokemembership_invalid_arguments"))
        return

    user_id_or_email = message.command[1]
    if user_id_or_email.isdigit():
        user = await bot.db.user.get(int(user_id_or_email))
    else:
        user = await bot.db.user.get_by_email(user_id_or_email)

    if user is None:
        await message.reply(
            lp("revokemembership_user_not_found").format(user_id=user_id_or_email)
        )
        return

    if not user.is_membership_active():
        await message.reply(
            lp("revokemembership_user_no_active_membership").format(user_id=user.id)
        )
        return

    await bot.db.user.revoke_membership(user.id)
    await message.reply(
        lp("revokemembership_success").format(user_id=user.id),
        disable_web_page_preview=True,
    )
