from pyrogram import filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from ..bot import PinkMusicBot


@PinkMusicBot.on_message(
    filters.text & (filters.private | filters.group) & filters.command("countries")
)
async def message(bot: PinkMusicBot, message: Message):
    lp = bot.get_lp(message)

    reply_markup = []
    for interface in bot.apple_music_interfaces.values():
        storefront = interface.apple_music_api.storefront
        reply_markup.append(
            [
                InlineKeyboardButton(
                    storefront.upper(),
                    url=f"https://music.apple.com/{storefront.lower()}/new",
                )
            ]
        )

    await message.reply(
        lp("countries"),
        reply_markup=InlineKeyboardMarkup(reply_markup),
    )
