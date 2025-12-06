from pyrogram import filters
from pyrogram.types import Message

from ..bot import PinkMusicBot
from ..constants import SONG_CODEC_MAP


@PinkMusicBot.on_message(
    filters.text & (filters.private | filters.group) & filters.command("me")
)
async def message(bot: PinkMusicBot, message: Message):
    await bot.ensure_user_exists(message)
    await bot.add_free_daily_credits(message)
    lp = bot.get_lp(message)

    user = await bot.db.user.get(message.from_user.id)
    await message.reply(
        lp("me").format(
            user_id=user.id,
            credits=user.credits,
            membership_due_date=(
                user.membership_due_date.strftime("%Y-%m-%d")
                if user.active_membership
                else lp("membership_unactive")
            ),
            songs_downloaded=user.songs_downloaded,
            music_videos_downloaded=user.music_videos_downloaded,
            synced_lyrics_file_upload=(
                lp("enabled") if user.synced_lyrics_file_upload else lp("disabled")
            ),
            song_codec=SONG_CODEC_MAP[user.song_codec.value],
            fourk_download=(lp("enabled") if user.fourk_download else lp("disabled")),
            search_country=user.search_country,
        )
    )
