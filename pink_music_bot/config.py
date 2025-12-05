import os
import inspect
from gamdl.api import AppleMusicApi
from gamdl.downloader import (
    AppleMusicBaseDownloader,
    DownloadMode,
    RemuxMode,
    CoverFormat,
    RemuxFormatMusicVideo,
    AppleMusicSongDownloader,
    AppleMusicMusicVideoDownloader,
)
from gamdl.interface import SyncedLyricsFormat

from dotenv import load_dotenv

api_create_from_netscape_cookies_sig = inspect.signature(
    AppleMusicApi.create_from_netscape_cookies
)
base_downloader_sig = inspect.signature(AppleMusicBaseDownloader.__init__)
song_downloader_sig = inspect.signature(AppleMusicSongDownloader.__init__)
music_video_downloader_sig = inspect.signature(AppleMusicMusicVideoDownloader.__init__)

load_dotenv()

api_id = os.environ["API_ID"]
api_hash = os.environ["API_HASH"]
bot_token = os.environ["BOT_TOKEN"]
max_concurrent_transmissions = int(os.environ.get("MAX_CONCURRENT_TRANSMISSIONS", 6))
database_url = os.environ.get("DATABASE_URL", "sqlite+aiosqlite:///pink_music_bot.db")
force_english = bool(os.environ.get("FORCE_ENGLISH"))
free_daily_credits = int(os.environ.get("FREE_DAILY_CREDITS", 50))
admin_user_id = int(os.environ["ADMIN_USER_ID"])
media_user_tokens = os.environ["MEDIA_USER_TOKENS"].split(":")
wrapper_account_url = os.environ.get("WRAPPER_ACCOUNT_URL")
api_language = os.environ.get(
    "API_LANGUAGE",
    api_create_from_netscape_cookies_sig.parameters["language"].default,
)
credit_api_url = os.environ.get("CREDIT_API_URL", "https://example.com")
kofi_verification_token = os.environ.get(
    "KOFI_VERIFICATION_TOKEN",
    "11111111-2222-3333-3333-444444444444",
)
kofi_shop_id = os.environ.get("KOFI_SHOP_ID", "abcde12345")
kofi_url = os.environ.get("KOFI_URL", "example.com")
download_timeout = int(os.environ.get("DOWNLOAD_TIMEOUT", 300))
song_cache_chat_id = int(os.environ["SONG_CACHE_CHAT_ID"])
music_video_cache_id = int(
    os.environ.get("MUSIC_VIDEO_CACHE_CHAT_ID", song_cache_chat_id)
)

downloader_temp_path = os.environ.get(
    "DOWNLOADER_TEMP_PATH",
    base_downloader_sig.parameters["temp_path"].default,
)
downloader_ffmpeg_path = os.environ.get(
    "DOWNLOADER_FFMPEG_PATH",
    base_downloader_sig.parameters["ffmpeg_path"].default,
)
downloader_mp4box_path = os.environ.get(
    "DOWNLOADER_MP4BOX_PATH",
    base_downloader_sig.parameters["mp4box_path"].default,
)
downloader_mp4decrypt_path = os.environ.get(
    "DOWNLOADER_MP4DECRYPT_PATH",
    base_downloader_sig.parameters["mp4decrypt_path"].default,
)
downloader_nm3u8dlre_path = os.environ.get(
    "DOWNLOADER_NM3U8DLRE_PATH",
    base_downloader_sig.parameters["nm3u8dlre_path"].default,
)
downloader_download_mode = DownloadMode(
    os.environ.get(
        "DOWNLOADER_DOWNLOAD_MODE",
        base_downloader_sig.parameters["download_mode"].default,
    )
)
downloader_remux_mode = RemuxMode(
    os.environ.get(
        "DOWNLOADER_REMUX_MODE",
        base_downloader_sig.parameters["remux_mode"].default,
    )
)
downloader_cover_format = CoverFormat(
    os.environ.get(
        "DOWNLOADER_COVER_FORMAT",
        base_downloader_sig.parameters["cover_format"].default,
    )
)
downloader_single_disc_file_template = os.environ.get(
    "DOWNLOADER_SINGLE_DISC_FILE_TEMPLATE",
    base_downloader_sig.parameters["single_disc_file_template"].default,
)
downloader_multi_disc_file_template = os.environ.get(
    "DOWNLOADER_MULTI_DISC_FILE_TEMPLATE",
    base_downloader_sig.parameters["multi_disc_file_template"].default,
)
downloader_no_album_file_template = os.environ.get(
    "DOWNLOADER_NO_ALBUM_FILE_TEMPLATE",
    base_downloader_sig.parameters["no_album_file_template"].default,
)
downloader_date_tag_template = os.environ.get(
    "DOWNLOADER_DATE_TAG_TEMPLATE",
    base_downloader_sig.parameters["date_tag_template"].default,
)
downloader_exclude_tags = (
    os.environ["DOWNLOADER_EXCLUDE_TAGS"].split(",")
    if "DOWNLOADER_EXCLUDE_TAGS" in os.environ
    else base_downloader_sig.parameters["exclude_tags"].default
)
downloader_truncate = (
    int(os.environ["DOWNLOADER_TRUNCATE"])
    if "DOWNLOADER_TRUNCATE" in os.environ
    else base_downloader_sig.parameters["truncate"].default
)
downloader_cover_size = (
    int(os.environ["DOWNLOADER_COVER_SIZE"])
    if "DOWNLOADER_COVER_SIZE" in os.environ
    else base_downloader_sig.parameters["cover_size"].default
)
downloader_exclude_tags = (
    os.environ.get("DOWNLOADER_EXCLUDE_TAGS", "").split(",")
    if "DOWNLOADER_EXCLUDE_TAGS" in os.environ
    else base_downloader_sig.parameters["exclude_tags"].default
)
downloader_synced_lyrics_format = SyncedLyricsFormat(
    os.environ.get(
        "DOWNLOADER_SYNCED_LYRICS_FORMAT",
        song_downloader_sig.parameters["synced_lyrics_format"].default,
    )
)
downloader_music_video_remux_format = RemuxFormatMusicVideo(
    os.environ.get(
        "DOWNLOADER_MUSIC_VIDEO_REMUX_FORMAT",
        music_video_downloader_sig.parameters["remux_format"].default,
    )
)
downloader_amdecrypt_path = os.environ.get(
    "DOWNLOADER_AMDECRYPT_PATH",
    base_downloader_sig.parameters["amdecrypt_path"].default,
)
downloader_wrapper_decrypt_ip = os.environ.get(
    "DOWNLOADER_WRAPPER_DECRYPT_IP",
    base_downloader_sig.parameters["wrapper_decrypt_ip"].default,
)
