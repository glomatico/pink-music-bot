import logging

from gamdl.downloader import (
    AppleMusicBaseDownloader,
    AppleMusicDownloader,
    AppleMusicMusicVideoDownloader,
    AppleMusicSongDownloader,
)
from gamdl.downloader.constants import (
    ALBUM_MEDIA_TYPE,
    MUSIC_VIDEO_MEDIA_TYPE,
    PLAYLIST_MEDIA_TYPE,
    SONG_MEDIA_TYPE,
    VALID_URL_PATTERN,
)
from gamdl.interface import (
    AppleMusicMusicVideoInterface,
    AppleMusicSongInterface,
    MusicVideoResolution,
)
from pyrogram import filters
from pyrogram.types import Message

from ..bot import PinkMusicBot

logger = logging.getLogger(__name__)


@PinkMusicBot.on_message(
    filters.text & (filters.private | filters.group) & filters.command("uncache")
)
async def message(bot: PinkMusicBot, message: Message):
    lp = bot.get_lp(message)
    await bot.ensure_user_exists(message)

    if not bot.is_admin(message):
        await message.reply(lp("not_admin"))
        return

    await _message(bot, message, lp)


async def _message(bot: PinkMusicBot, message: Message, lp):
    user = await bot.db.user.get(message.from_user.id)

    filtered_url_list = [
        word for word in message.command[1:] if VALID_URL_PATTERN.match(word)
    ][:3]

    if not filtered_url_list:
        await message.reply(lp("download_no_url"))
        return

    base_downloader = AppleMusicBaseDownloader()
    song_downloader = AppleMusicSongDownloader(
        base_downloader=base_downloader,
        interface=None,
    )
    music_video_downloader = AppleMusicMusicVideoDownloader(
        base_downloader=base_downloader,
        interface=None,
        resolution=(
            MusicVideoResolution.R2160P
            if user.fourk_download
            else MusicVideoResolution.R1080P
        ),
    )
    downloader = AppleMusicDownloader(
        interface=None,
        base_downloader=base_downloader,
        song_downloader=song_downloader,
        music_video_downloader=music_video_downloader,
        uploaded_video_downloader=None,
    )

    error_count = 0

    for url in filtered_url_list:
        url_message = await message.reply(
            lp("download_url_processing").format(url=url),
            disable_web_page_preview=True,
        )
        url_download_queue = None

        try:
            url_info = downloader.get_url_info(url)

            if url_info.type not in {
                *SONG_MEDIA_TYPE,
                *ALBUM_MEDIA_TYPE,
                *PLAYLIST_MEDIA_TYPE,
                *MUSIC_VIDEO_MEDIA_TYPE,
            }:
                await url_message.edit(
                    lp("download_unsupported_url").format(media_type=url_info.type),
                    disable_web_page_preview=True,
                )
                continue

            if url_info.storefront.lower() not in bot.apple_music_interfaces:
                interface = next(iter(bot.apple_music_interfaces.values()))
                await message.reply(
                    lp("download_unsupported_country").format(
                        url=url,
                        default_country=interface.apple_music_api.storefront.upper(),
                    ),
                    disable_web_page_preview=True,
                )
            else:
                interface = bot.apple_music_interfaces[url_info.storefront.lower()]

            interface = bot.apple_music_interfaces.get(
                url_info.storefront.lower(),
                next(iter(bot.apple_music_interfaces.values())),
            )
            song_interface = AppleMusicSongInterface(interface)
            music_video_interface = AppleMusicMusicVideoInterface(interface)

            song_downloader.interface = song_interface
            music_video_downloader.interface = music_video_interface
            downloader.interface = interface

            downloader.flat_filter = lambda _: True

            url_download_queue = await downloader.get_download_queue(url_info)
        except Exception:
            logger.exception(f"{url}@{message.from_user.id}")
            error_count += 1
            await url_message.edit(
                lp("download_url_processing_fail").format(url=url),
                disable_web_page_preview=True,
            )
            continue

        if not url_download_queue:
            await url_message.edit(
                lp("download_nothing_found").format(url=url),
                disable_web_page_preview=True,
            )

        await url_message.edit(
            lp("uncache_start").format(total=len(url_download_queue))
        )

        for download_item in url_download_queue:
            try:
                if isinstance(download_item, Exception):
                    media_id = "Unknown ID"
                    media_title = "Unknown Title"
                    raise download_item
                else:
                    media_id = download_item.media_metadata["id"]
                    media_title = download_item.media_metadata["attributes"]["name"]

                if download_item.media_metadata["type"] in SONG_MEDIA_TYPE:
                    delete_result = await bot.db.song.delete(
                        download_item.media_metadata["id"]
                    )
                else:
                    delete_result = await bot.db.music_video.delete(
                        download_item.media_metadata["id"],
                        user.fourk_download,
                    )

                if delete_result:
                    await message.reply(lp("uncache_success").format(title=media_title))
                else:
                    await message.reply(
                        lp("uncache_not_cached").format(title=media_title)
                    )
            except Exception:
                logger.exception(f"{media_id}@{message.from_user.id}")
                error_count += 1
                await message.reply(lp("uncache_fail").format(title=media_title))
                continue

    await message.reply(lp("uncache_complete"))
