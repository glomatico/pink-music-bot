import asyncio
import logging

from .bot import PinkMusicBot
from .config import (
    admin_user_id,
    api_hash,
    api_id,
    api_language,
    bot_token,
    credit_api_url,
    database_url,
    download_timeout,
    downloader_amdecrypt_path,
    downloader_cover_format,
    downloader_cover_size,
    downloader_date_tag_template,
    downloader_download_mode,
    downloader_exclude_tags,
    downloader_ffmpeg_path,
    downloader_mp4box_path,
    downloader_mp4decrypt_path,
    downloader_multi_disc_file_template,
    downloader_music_video_remux_format,
    downloader_nm3u8dlre_path,
    downloader_no_album_file_template,
    downloader_remux_mode,
    downloader_single_disc_file_template,
    downloader_synced_lyrics_format,
    downloader_temp_path,
    downloader_truncate,
    downloader_wrapper_decrypt_ip,
    force_english,
    free_daily_credits,
    kofi_shop_id,
    kofi_url,
    kofi_verification_token,
    max_concurrent_transmissions,
    media_user_tokens,
    music_video_cache_id,
    song_cache_chat_id,
    wrapper_account_url,
)

logger = logging.getLogger(__package__)


async def main():
    logging.getLogger("pyrogram").setLevel(logging.ERROR)
    logging.basicConfig(
        format="[%(asctime)s - %(levelname)s - %(name)s] %(message)s",
    )
    logger.setLevel(logging.INFO)

    await PinkMusicBot.start_(
        api_id=api_id,
        api_hash=api_hash,
        bot_token=bot_token,
        max_concurrent_transmissions=max_concurrent_transmissions,
        database_url=database_url,
        force_english=force_english,
        free_daily_credits=free_daily_credits,
        admin_user_id=admin_user_id,
        media_user_tokens=media_user_tokens,
        wrapper_account_url=wrapper_account_url,
        api_language=api_language,
        credit_api_url=credit_api_url,
        kofi_verification_token=kofi_verification_token,
        kofi_shop_id=kofi_shop_id,
        kofi_url=kofi_url,
        download_timeout=download_timeout,
        song_cache_chat_id=song_cache_chat_id,
        music_video_cache_chat_id=music_video_cache_id,
        downloader_temp_path=downloader_temp_path,
        downloader_ffmpeg_path=downloader_ffmpeg_path,
        downloader_mp4box_path=downloader_mp4box_path,
        downloader_mp4decrypt_path=downloader_mp4decrypt_path,
        downloader_nm3u8dlre_path=downloader_nm3u8dlre_path,
        downloader_amdecrypt_path=downloader_amdecrypt_path,
        downloader_wrapper_decrypt_ip=downloader_wrapper_decrypt_ip,
        downloader_download_mode=downloader_download_mode,
        downloader_remux_mode=downloader_remux_mode,
        downloader_cover_format=downloader_cover_format,
        downloader_cover_size=downloader_cover_size,
        downloader_single_disc_file_template=downloader_single_disc_file_template,
        downloader_multi_disc_file_template=downloader_multi_disc_file_template,
        downloader_no_album_file_template=downloader_no_album_file_template,
        downloader_date_tag_template=downloader_date_tag_template,
        downloader_exclude_tags=downloader_exclude_tags,
        downloader_truncate=downloader_truncate,
        downloader_synced_lyrics_format=downloader_synced_lyrics_format,
        downloader_music_video_remux_format=downloader_music_video_remux_format,
    )


asyncio.run(main())
