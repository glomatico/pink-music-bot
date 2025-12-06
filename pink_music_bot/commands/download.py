import asyncio
import logging
import os
from io import BytesIO

from gamdl.downloader import (
    AppleMusicBaseDownloader,
    AppleMusicDownloader,
    AppleMusicMusicVideoDownloader,
    AppleMusicSongDownloader,
    DownloadItem,
    FormatNotAvailable,
    NotStreamable,
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
    SongCodec,
)
from pyrogram import filters
from pyrogram.types import Message

from ..bot import PinkMusicBot
from ..database import MusicVideo, Song

logger = logging.getLogger(__name__)


async def enqueue_upload_audio(
    bot: PinkMusicBot,
    high_priority: bool,
    **kwargs,
) -> Message:
    priority = 0 if high_priority else 1
    async with bot.upload_priority_semaphore.acquire(priority):
        return await bot.send_audio(**kwargs)


async def enqueue_upload_video(
    bot: PinkMusicBot,
    high_priority: bool,
    **kwargs,
) -> Message:
    priority = 0 if high_priority else 1
    async with bot.upload_priority_semaphore.acquire(priority):
        return await bot.send_video(**kwargs)


async def enqueue_upload_document(
    bot: PinkMusicBot,
    high_priority: bool,
    **kwargs,
) -> Message:
    priority = 0 if high_priority else 1
    async with bot.upload_priority_semaphore.acquire(priority):
        return await bot.send_document(**kwargs)


async def enqueue_download(
    bot: PinkMusicBot,
    downloader: AppleMusicDownloader,
    download_item: DownloadItem,
    use_wrapper: bool,
    high_priority: bool,
) -> DownloadItem:
    priority = 0 if high_priority else 1

    if use_wrapper:
        downloader.base_downloader.use_wrapper = True

        async with bot.wrapper_locker:
            async with bot.download_priority_semaphore.acquire(priority):
                result = await asyncio.wait_for(
                    downloader.download(download_item),
                    timeout=bot.download_timeout,
                )
            await asyncio.sleep(5)

    else:
        downloader.base_downloader.use_wrapper = False

        async with bot.download_priority_semaphore.acquire(priority):
            result = await asyncio.wait_for(
                downloader.download(download_item),
                timeout=bot.download_timeout,
            )

    return result


@PinkMusicBot.on_message(
    filters.text
    & (filters.private | filters.group)
    & (filters.command("download") | filters.regex(r"^(?!/)"))
)
async def message(bot: PinkMusicBot, message: Message):
    lp = bot.get_lp(message)
    await bot.ensure_user_exists(message)
    await bot.add_free_daily_credits(message)

    if bot.user_locker.is_user_locked(message.from_user.id):
        await message.reply(lp("download_pending"))
        return

    async with bot.user_locker.acquire_user_lock(message.from_user.id):
        await _message(bot, message, lp)


async def _message(bot: PinkMusicBot, message: Message, lp):
    if await bot.is_under_maintenance(message):
        return

    user = await bot.db.user.get(message.from_user.id)

    if user.credits <= 0 and not user.is_membership_active():
        await message.reply(lp("download_no_credits"))
        return

    if not user.is_membership_active() and user.song_codec != SongCodec.AAC_LEGACY:
        await message.reply(lp("download_songcodec_fallback"))
        user.song_codec = SongCodec.AAC_LEGACY
        await bot.db.user.update_song_codec(
            user.id,
            SongCodec.AAC_LEGACY,
        )

    filtered_url_list = [
        word for word in message.text.split() if VALID_URL_PATTERN.match(word)
    ][:3]

    if not filtered_url_list:
        await message.reply(lp("download_no_url"))
        return

    base_downloader = AppleMusicBaseDownloader(
        temp_path=bot.downloader_temp_path,
        ffmpeg_path=bot.downloader_ffmpeg_path,
        mp4box_path=bot.downloader_mp4box_path,
        mp4decrypt_path=bot.downloader_mp4decrypt_path,
        nm3u8dlre_path=bot.downloader_nm3u8dlre_path,
        amdecrypt_path=bot.downloader_amdecrypt_path,
        wrapper_decrypt_ip=bot.downloader_wrapper_decrypt_ip,
        use_wrapper=user.song_codec != SongCodec.AAC_LEGACY,
        download_mode=bot.downloader_download_mode,
        remux_mode=bot.downloader_remux_mode,
        cover_format=bot.downloader_cover_format,
        cover_size=bot.downloader_cover_size,
        single_disc_file_template=bot.downloader_single_disc_file_template,
        multi_disc_file_template=bot.downloader_multi_disc_file_template,
        no_album_file_template=bot.downloader_no_album_file_template,
        date_tag_template=bot.downloader_date_tag_template,
        exclude_tags=bot.downloader_exclude_tags,
        truncate=bot.downloader_truncate,
        silent=True,
    )
    song_downloader = AppleMusicSongDownloader(
        base_downloader=base_downloader,
        interface=None,
        codec=user.song_codec,
        synced_lyrics_format=bot.downloader_synced_lyrics_format,
    )
    music_video_downloader = AppleMusicMusicVideoDownloader(
        base_downloader=base_downloader,
        interface=None,
        remux_format=bot.downloader_music_video_remux_format,
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
        skip_processing=True,
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

            if (
                user.song_codec != SongCodec.AAC_LEGACY
                and url_info.type not in MUSIC_VIDEO_MEDIA_TYPE
            ):
                interface = bot.apple_music_wrapper_interface
                if (
                    url_info.storefront.lower()
                    != bot.apple_music_wrapper_interface.apple_music_api.storefront.lower()
                ):
                    await message.reply(
                        lp("download_unsupported_wrapper_country").format(
                            url=url,
                            supported_country=bot.apple_music_wrapper_interface.apple_music_api.storefront.upper(),
                            supported_country_url=(
                                f"https://music.apple.com/{bot.apple_music_wrapper_interface.apple_music_api.storefront.lower()}/new"
                            ),
                        ),
                        disable_web_page_preview=True,
                    )

            else:
                interface = bot.apple_music_interfaces.get(
                    url_info.storefront.lower(),
                    next(iter(bot.apple_music_interfaces.values())),
                )
                if url_info.storefront.lower() not in bot.apple_music_interfaces:
                    await message.reply(
                        lp("download_unsupported_country").format(
                            url=url,
                            default_country=interface.apple_music_api.storefront.upper(),
                        ),
                        disable_web_page_preview=True,
                    )

            song_interface = AppleMusicSongInterface(interface)
            music_video_interface = AppleMusicMusicVideoInterface(interface)

            song_downloader.interface = song_interface
            music_video_downloader.interface = music_video_interface
            downloader.interface = interface

            async def flat_filter(media_metadata: dict):
                if media_metadata["type"] in SONG_MEDIA_TYPE:
                    return await bot.db.song.get(
                        media_metadata["id"],
                        user.song_codec,
                    )

                else:
                    if not user.is_membership_active():
                        return lp("download_music_video_requires_membership")

                    return await bot.db.music_video.get(
                        media_metadata["id"],
                        fourk=(
                            True
                            if user.fourk_download
                            and media_metadata["attributes"]["has4K"]
                            else False
                        ),
                    )

            downloader.flat_filter = flat_filter

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
            return

        await url_message.edit(
            lp("download_start").format(total=len(url_download_queue))
        )

        for download_item in url_download_queue:
            skip_credit_deduct = user.is_membership_active()
            media_id = download_item.media_metadata["id"]
            media_title = download_item.media_metadata["attributes"]["name"]

            if await bot.is_under_maintenance(message):
                return

            if user.credits <= 0 and not user.is_membership_active():
                await message.reply(lp("download_no_credits"))
                return

            if isinstance(download_item.flat_filter_result, str):
                await message.reply(download_item.flat_filter_result)
                continue

            try:
                if isinstance(download_item.flat_filter_result, Song):
                    database_entry = download_item.flat_filter_result
                    song_cache_message = await bot.get_messages(
                        bot.song_cache_chat_id,
                        database_entry.message_id_song,
                    )

                    if database_entry.message_id_synced_lyrics:
                        synced_lyrics_cache_message = await bot.get_messages(
                            bot.song_cache_chat_id,
                            database_entry.message_id_synced_lyrics,
                        )
                    else:
                        synced_lyrics_cache_message = None

                    # Song cache is valid if:
                    cache_is_valid = (
                        # - The song message exists
                        not song_cache_message.empty
                        # - The lyrics message exists if lyrics are available
                        and not (
                            not database_entry.message_id_synced_lyrics
                            and (download_item.lyrics and download_item.lyrics.synced)
                        )
                        # - The lyrics message exists if lyrics are stored
                        and (
                            not database_entry.message_id_synced_lyrics
                            or (
                                synced_lyrics_cache_message
                                and not synced_lyrics_cache_message.empty
                            )
                        )
                        # - The song message caption contains the ID
                        and song_cache_message.caption.find(
                            download_item.media_metadata["id"]
                        )
                        != -1
                    )

                    if cache_is_valid:
                        await bot.copy_message(
                            message.chat.id,
                            bot.song_cache_chat_id,
                            database_entry.message_id_song,
                            "",
                        )
                        if (
                            database_entry.message_id_synced_lyrics
                            and synced_lyrics_cache_message
                            and not synced_lyrics_cache_message.empty
                            and user.synced_lyrics_file_upload
                        ):
                            await bot.copy_message(
                                message.chat.id,
                                bot.song_cache_chat_id,
                                database_entry.message_id_synced_lyrics,
                                "",
                            )

                        await bot.db.user.increment_songs_downloaded(
                            message.from_user.id
                        )
                        continue

                if isinstance(download_item.flat_filter_result, MusicVideo):
                    database_entry = download_item.flat_filter_result

                    if database_entry.too_large:
                        await message.reply(
                            lp("download_too_large").format(title=media_title)
                        )
                        continue

                    music_video_cache_message = await bot.get_messages(
                        bot.song_cache_chat_id,
                        database_entry.message_id,
                    )

                    # Music video cache is valid if:
                    cache_is_valid = (
                        # - The music video message exists
                        not music_video_cache_message.empty
                        # - The music video message caption contains the ID
                        and music_video_cache_message.caption.find(
                            download_item.media_metadata["id"]
                        )
                        != -1
                    )

                    if cache_is_valid:
                        await bot.copy_message(
                            message.chat.id,
                            bot.song_cache_chat_id,
                            database_entry.message_id,
                            "",
                        )

                        await bot.db.user.increment_music_videos_downloaded(
                            message.from_user.id
                        )
                        continue

                download_item = await enqueue_download(
                    bot,
                    downloader,
                    download_item,
                    user.song_codec != SongCodec.AAC_LEGACY
                    and download_item.media_metadata["type"] in SONG_MEDIA_TYPE,
                    user.is_membership_active(),
                )

                if download_item.cover_url_template:
                    cover_url_telegram = base_downloader.format_cover_url(
                        download_item.cover_url_template,
                        300,
                        "jpg",
                    )
                    cover_data = await base_downloader.get_cover_bytes(
                        cover_url_telegram,
                    )
                    cover_bytes_telegram = BytesIO(cover_data) if cover_data else None
                else:
                    cover_bytes_telegram = None

                if download_item.media_metadata["type"] in SONG_MEDIA_TYPE:
                    caption_song = " ".join(
                        [
                            f"<code>{download_item.media_metadata['id']}</code>",
                            f"<code>{interface.apple_music_api.storefront.upper()}</code>",
                            f"<code>{user.song_codec.value}</code>",
                            "<code>song</code>",
                        ]
                    )
                    if download_item.lyrics and download_item.lyrics.synced:
                        caption_lyrics = " ".join(
                            [
                                f"<code>{download_item.media_metadata['id']}</code>",
                                f"<code>{interface.apple_music_api.storefront.upper()}</code>",
                                f"<code>{user.song_codec.value}</code>",
                                "<code>lyrics</code>",
                            ]
                        )
                    else:
                        caption_lyrics = None

                    with open(download_item.staged_path, "rb") as f:
                        audio_bytes = BytesIO(f.read())

                    message_song = await enqueue_upload_audio(
                        bot,
                        user.is_membership_active(),
                        chat_id=bot.song_cache_chat_id,
                        audio=audio_bytes,
                        thumb=cover_bytes_telegram,
                        caption=caption_song,
                        duration=download_item.media_metadata["attributes"][
                            "durationInMillis"
                        ]
                        // 1000,
                        performer=download_item.media_tags.artist,
                        title=download_item.media_tags.title,
                        file_name=os.path.basename(download_item.final_path),
                    )
                    if caption_lyrics:
                        message_lyrics = await enqueue_upload_document(
                            bot,
                            user.is_membership_active(),
                            chat_id=bot.song_cache_chat_id,
                            document=BytesIO(
                                download_item.lyrics.synced.encode("utf-8")
                            ),
                            caption=caption_lyrics,
                            file_name=os.path.basename(
                                song_downloader.get_lyrics_synced_path(
                                    download_item.final_path
                                )
                            ),
                        )
                    else:
                        message_lyrics = None

                    await bot.db.song.add_if_not_exists(
                        download_item.media_metadata["id"],
                        user.song_codec,
                        message_song.id,
                        message_lyrics.id if message_lyrics else None,
                    )

                    await bot.copy_message(
                        message.chat.id,
                        bot.song_cache_chat_id,
                        message_song.id,
                        "",
                    )
                    if message_lyrics and user.synced_lyrics_file_upload:
                        await bot.copy_message(
                            message.chat.id,
                            bot.song_cache_chat_id,
                            message_lyrics.id,
                            "",
                        )

                    await bot.db.user.increment_songs_downloaded(message.from_user.id)

                else:
                    file_size = os.path.getsize(download_item.staged_path)
                    max_file_size = 2000 * 1024 * 1024
                    fourk = (
                        user.fourk_download
                        and download_item.media_metadata["attributes"]["has4K"]
                    )

                    if file_size > max_file_size:
                        await message.reply(
                            lp("download_too_large").format(title=media_title)
                        )
                        await bot.db.music_video.add_if_not_exists(
                            download_item.media_metadata["id"],
                            fourk,
                            None,
                            True,
                        )
                        continue

                    caption_mv = " ".join(
                        [
                            f"<code>{download_item.media_metadata['id']}</code>",
                            f"<code>{interface.apple_music_api.storefront.upper()}</code>",
                            f"<code>{'uhd' if fourk else 'hd'}</code>",
                            "<code>music_video</code>",
                        ]
                    )

                    with open(download_item.staged_path, "rb") as f:
                        video_bytes = BytesIO(f.read())

                    message_music_video = await enqueue_upload_video(
                        bot,
                        user.is_membership_active(),
                        chat_id=bot.music_video_cache_chat_id,
                        video=video_bytes,
                        thumb=cover_bytes_telegram,
                        caption=caption_mv,
                        duration=download_item.media_metadata["attributes"][
                            "durationInMillis"
                        ]
                        // 1000,
                        file_name=os.path.basename(download_item.final_path),
                        supports_streaming=True,
                    )

                    await bot.db.music_video.add_if_not_exists(
                        download_item.media_metadata["id"],
                        fourk,
                        message_music_video.id,
                    )

                    await bot.copy_message(
                        message.chat.id,
                        bot.music_video_cache_chat_id,
                        message_music_video.id,
                        "",
                    )
                    await bot.db.user.increment_music_videos_downloaded(
                        message.from_user.id
                    )
            except FormatNotAvailable:
                await message.reply(
                    lp("download_format_unavailable").format(title=media_title)
                )
                continue
            except NotStreamable:
                await message.reply(
                    lp("download_unstremeable").format(title=media_title)
                )
                continue
            except asyncio.TimeoutError:
                await message.reply(lp("download_timeout"))
                return
            except Exception:
                logger.exception(f"{media_id}@{message.from_user.id}")
                error_count += 1
                skip_credit_deduct = True
                await message.reply(lp("download_fail").format(title=media_title))
                continue
            finally:
                if isinstance(download_item, DownloadItem):
                    base_downloader.cleanup_temp(download_item.random_uuid)

                if not isinstance(
                    download_item.flat_filter_result, Song
                ) or not isinstance(download_item.flat_filter_result, MusicVideo):
                    await asyncio.sleep(5)

                if not skip_credit_deduct:
                    user.credits -= 1
                    await bot.db.user.deduct_credits(
                        message.from_user.id,
                        1,
                    )

    if error_count == 0:
        await message.reply(lp("download_complete"))
    else:
        await message.reply(lp("download_complete_but"))
