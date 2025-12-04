from pyrogram import filters
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from ..bot import PinkMusicBot


def get_reply_markup(
    current_country: str, apple_music_interfaces: dict
) -> InlineKeyboardMarkup:
    reply_markup = []
    for country in apple_music_interfaces.keys():
        reply_markup.append(
            [
                InlineKeyboardButton(
                    ("✅ " if country.upper() == current_country else "")
                    + country.upper(),
                    callback_data=f"searchcountry:{country.upper()}",
                )
            ]
        )

    return InlineKeyboardMarkup(reply_markup)


@PinkMusicBot.on_message(
    filters.text & (filters.private | filters.group) & filters.command("searchcountry")
)
async def message(bot: PinkMusicBot, message: Message):
    await bot.ensure_user_exists(message)
    lp = bot.get_lp(message)
    user = await bot.db.user.get(message.from_user.id)

    await message.reply(
        lp("search_country_choose"),
        reply_markup=get_reply_markup(user.search_country, bot.apple_music_interfaces),
    )


@PinkMusicBot.on_callback_query(filters.regex("^searchcountry:"))
async def callback_query(bot: PinkMusicBot, callback: CallbackQuery):
    lp = bot.get_lp(callback)

    current_country = callback.data.split(":")[-1]
    await bot.db.user.update_search_country(callback.from_user.id, current_country)

    await callback.answer(
        lp("search_country_changed").format(search_country=current_country)
    )
    await callback.edit_message_reply_markup(
        reply_markup=get_reply_markup(current_country, bot.apple_music_interfaces)
    )
