import logging
from datetime import datetime, timedelta
from pathlib import Path

from pyrogram import filters
from pyrogram.types import Message

from ..bot import PinkMusicBot

logger = logging.getLogger(__name__)


@PinkMusicBot.on_message(
    filters.text
    & (filters.private | filters.group)
    & filters.command("givemembershipdays")
)
async def message(bot: PinkMusicBot, message: Message):
    if not bot.is_admin(message):
        return
    lp = bot.get_lp(message)

    if len(message.command) < 3:
        await message.reply(lp("givemembershipdays_invalid_arguments"))
        return

    user_id, days_str = message.command[1:3]
    try:
        user_id = int(user_id)
        days = int(days_str)
    except ValueError:
        await message.reply(lp("givemembershipdays_invalid_arguments"))
        return

    user = await bot.db.user.get(user_id)
    if user is None:
        await message.reply(
            lp("givemembershipdays_user_not_found").format(user_id=user_id)
        )
        return

    await bot.db.user.add_membership_days(user.id, days)
    await message.reply(
        lp("givemembershipdays_success").format(
            days=days,
            user_id=user.id,
        ),
        disable_web_page_preview=True,
    )
