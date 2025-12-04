from gamdl.interface import SongCodec
from pyrogram import filters
from pyrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
)

from ..bot import PinkMusicBot
from ..constants import SONG_CODEC_MAP


def get_reply_markup(current_song_codec: str) -> InlineKeyboardMarkup:
    reply_markup = []
    for key, value in SONG_CODEC_MAP.items():
        reply_markup.append(
            [
                InlineKeyboardButton(
                    ("✅ " if current_song_codec == key else "") + value,
                    callback_data=f"songcodec:{key}",
                )
            ]
        )

    return InlineKeyboardMarkup(reply_markup)


@PinkMusicBot.on_message(
    filters.text & (filters.private | filters.group) & filters.command("songcodec")
)
async def message(bot: PinkMusicBot, message: Message):
    await bot.ensure_user_exists(message)
    lp = bot.get_lp(message)
    user = await bot.db.user.get(message.from_user.id)
    if not user.is_membership_active():
        await message.reply(lp("songcodec_membership_required"))
        return

    await message.reply(
        lp("songcodec_choose"),
        reply_markup=get_reply_markup(user.song_codec.value),
    )


@PinkMusicBot.on_callback_query(filters.regex("^songcodec:"))
async def callback_query(bot: PinkMusicBot, callback: CallbackQuery):
    lp = bot.get_lp(callback)

    current_song_codec = callback.data.split(":")[-1]
    await bot.db.user.update_song_codec(
        callback.from_user.id,
        SongCodec(current_song_codec),
    )

    await callback.answer(
        lp("songcodec_changed").format(song_codec=SONG_CODEC_MAP[current_song_codec])
    )
    await callback.edit_message_reply_markup(
        reply_markup=get_reply_markup(current_song_codec)
    )
