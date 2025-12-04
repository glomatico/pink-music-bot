from pyrogram import filters
from pyrogram.types import Message

from ..bot import PinkMusicBot


@PinkMusicBot.on_message(
    filters.text & (filters.private | filters.group) & filters.command("membership")
)
async def message(bot: PinkMusicBot, message: Message):
    lp = bot.get_lp(message)

    wrapper_country = (
        bot.apple_music_wrapper_interface.apple_music_api.storefront.upper()
        if bot.apple_music_wrapper_interface
        else "N/A"
    )

    await message.reply(
        lp("membership").format(
            free_downloads=bot.free_daily_credits,
            wrapper_country=wrapper_country,
            kofi_url=bot.kofi_url,
        ),
        disable_web_page_preview=True,
    )
