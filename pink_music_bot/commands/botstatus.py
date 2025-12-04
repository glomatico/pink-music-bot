from pathlib import Path

from pyrogram import filters
from pyrogram.types import Message

from ..bot import PinkMusicBot


@PinkMusicBot.on_message(
    filters.text & (filters.private | filters.group) & filters.command("botstatus")
)
async def message(bot: PinkMusicBot, message: Message):
    await bot.ensure_user_exists(message)
    if not bot.is_admin(message):
        return
    lp = bot.get_lp(message)

    total_users = await bot.db.user.count()
    total_member_users = await bot.db.user.count_members()
    total_songs = await bot.db.song.count()
    total_music_videos = await bot.db.music_video.count()
    current_downloads = 0  # TODO: implement user_locker
    bot_lock = Path("lock").exists()

    await message.reply(
        lp("botstatus").format(
            total_users=total_users,
            total_member_users=total_member_users,
            total_songs=total_songs,
            total_music_videos=total_music_videos,
            current_downloads=current_downloads,
            bot_lock=lp("enabled") if bot_lock else lp("disabled"),
        )
    )
