import asyncio
import datetime
import logging
from pathlib import Path
from typing import Callable

from gamdl.api import AppleMusicApi, ItunesApi
from gamdl.downloader import CoverFormat, DownloadMode, RemuxFormatMusicVideo, RemuxMode
from gamdl.interface import AppleMusicInterface, SyncedLyricsFormat
from pyrogram import Client
from pyrogram.methods.utilities.idle import idle
from pyrogram.types import Message

from .database import Database
from .locale_parser import LocaleParser
from .priority_semaphore import PrioritySemaphore
from .user_locker import UserLocker

logger = logging.getLogger(__name__)


class PinkMusicBot(Client):
    def __init__(
        self,
        api_id: int,
        api_hash: str,
        bot_token: str,
        max_concurrent_transmissions: int,
        db: Database,
        lp: LocaleParser,
        free_daily_credits: int,
        admin_user_id: int,
        apple_music_interfaces: dict[str, AppleMusicInterface],
        apple_music_wrapper_interface: AppleMusicInterface,
        credit_api_url: str,
        kofi_verification_token: str,
        kofi_shop_id: str,
        kofi_url: str,
        user_locker: UserLocker,
        upload_priority_semaphore: PrioritySemaphore,
        download_priority_semaphore: PrioritySemaphore,
        wrapper_locker: asyncio.Lock,
        download_timeout: int,
        song_cache_chat_id: int,
        music_video_cache_chat_id: int,
        # Downloader params
        downloader_temp_path: str,
        downloader_ffmpeg_path: str,
        downloader_mp4box_path: str,
        downloader_mp4decrypt_path: str,
        downloader_nm3u8dlre_path: str,
        downloader_amdecrypt_path: str,
        downloader_wrapper_decrypt_ip: str,
        downloader_download_mode: DownloadMode,
        downloader_remux_mode: RemuxMode,
        downloader_cover_format: CoverFormat,
        downloader_cover_size: int,
        downloader_single_disc_file_template: str,
        downloader_multi_disc_file_template: str,
        downloader_no_album_file_template: str,
        downloader_date_tag_template: str,
        downloader_exclude_tags: list[str],
        downloader_truncate: int | None,
        downloader_synced_lyrics_format: SyncedLyricsFormat,
        downloader_music_video_remux_format: RemuxFormatMusicVideo,
    ) -> None:
        super().__init__(
            name=__package__,
            api_id=api_id,
            api_hash=api_hash,
            bot_token=bot_token,
            plugins=dict(root=f"{__package__}/commands"),
            workers=1200,
            max_concurrent_transmissions=max_concurrent_transmissions,
            sleep_threshold=60,
        )
        self.db = db
        self.lp = lp
        self.free_daily_credits = free_daily_credits
        self.admin_user_id = admin_user_id
        self.apple_music_interfaces = apple_music_interfaces
        self.apple_music_wrapper_interface = apple_music_wrapper_interface
        self.credit_api_url = credit_api_url
        self.kofi_verification_token = kofi_verification_token
        self.kofi_shop_id = kofi_shop_id
        self.kofi_url = kofi_url
        self.user_locker = user_locker
        self.upload_priority_semaphore = upload_priority_semaphore
        self.download_priority_semaphore = download_priority_semaphore
        self.wrapper_locker = wrapper_locker
        self.download_timeout = download_timeout
        self.song_cache_chat_id = song_cache_chat_id
        self.music_video_cache_chat_id = music_video_cache_chat_id
        # Downloader params
        self.downloader_temp_path = downloader_temp_path
        self.downloader_ffmpeg_path = downloader_ffmpeg_path
        self.downloader_mp4box_path = downloader_mp4box_path
        self.downloader_mp4decrypt_path = downloader_mp4decrypt_path
        self.downloader_nm3u8dlre_path = downloader_nm3u8dlre_path
        self.downloader_amdecrypt_path = downloader_amdecrypt_path
        self.downloader_wrapper_decrypt_ip = downloader_wrapper_decrypt_ip
        self.downloader_download_mode = downloader_download_mode
        self.downloader_remux_mode = downloader_remux_mode
        self.downloader_cover_format = downloader_cover_format
        self.downloader_cover_size = downloader_cover_size
        self.downloader_single_disc_file_template = downloader_single_disc_file_template
        self.downloader_multi_disc_file_template = downloader_multi_disc_file_template
        self.downloader_no_album_file_template = downloader_no_album_file_template
        self.downloader_date_tag_template = downloader_date_tag_template
        self.downloader_exclude_tags = downloader_exclude_tags
        self.downloader_truncate = downloader_truncate
        self.downloader_synced_lyrics_format = downloader_synced_lyrics_format
        self.downloader_music_video_remux_format = downloader_music_video_remux_format

    @classmethod
    async def start_(
        cls,
        api_id: int,
        api_hash: str,
        bot_token: str,
        max_concurrent_transmissions: int,
        database_url: str,
        force_english: bool,
        free_daily_credits: int,
        admin_user_id: int,
        media_user_tokens: list[int],
        wrapper_account_url: str,
        api_language: str,
        credit_api_url: str,
        kofi_verification_token: str,
        kofi_shop_id: str,
        kofi_url: str,
        download_timeout: int,
        song_cache_chat_id: int,
        music_video_cache_chat_id: int,
        # Downloader params
        downloader_temp_path: str,
        downloader_ffmpeg_path: str,
        downloader_mp4box_path: str,
        downloader_mp4decrypt_path: str,
        downloader_nm3u8dlre_path: str,
        downloader_amdecrypt_path: str,
        downloader_wrapper_decrypt_ip: str,
        downloader_download_mode: DownloadMode,
        downloader_remux_mode: RemuxMode,
        downloader_cover_format: CoverFormat,
        downloader_cover_size: int,
        downloader_single_disc_file_template: str,
        downloader_multi_disc_file_template: str,
        downloader_no_album_file_template: str,
        downloader_date_tag_template: str,
        downloader_exclude_tags: list[str],
        downloader_truncate: int | None,
        downloader_synced_lyrics_format: SyncedLyricsFormat,
        downloader_music_video_remux_format: RemuxFormatMusicVideo,
    ) -> None:
        lp = LocaleParser(
            f"{__package__}/locale",
            force_fallback=force_english,
        )

        logger.info("Starting database")
        db = await Database.create(database_url)

        logger.info("Starting Apple Music interfaces")
        apple_music_interfaces = {}
        for media_user_token in media_user_tokens:
            try:
                apple_music_api = await AppleMusicApi.create(
                    media_user_token=media_user_token,
                    language=api_language,
                )
                assert apple_music_api.active_subscription

                itunes_api = ItunesApi(
                    storefront=apple_music_api.storefront,
                    language=api_language,
                )

                interface = AppleMusicInterface(
                    apple_music_api=apple_music_api,
                    itunes_api=itunes_api,
                )
                apple_music_interfaces[apple_music_api.storefront.lower()] = interface
            except Exception as e:
                raise RuntimeError(
                    f"Failed to setup API for media user token '{media_user_token}'"
                )

        if wrapper_account_url is not None:
            apple_music_wrapper_api = await AppleMusicApi.create_from_wrapper(
                wrapper_account_url=wrapper_account_url,
                language=api_language,
            )
            itunes_wrapper_api = ItunesApi(
                storefront=apple_music_wrapper_api.storefront,
                language=api_language,
            )
            apple_music_wrapper_interface = AppleMusicInterface(
                apple_music_api=apple_music_wrapper_api,
                itunes_api=itunes_wrapper_api,
            )
        else:
            apple_music_wrapper_interface = None

        logger.info("Starting bot")
        bot = cls(
            api_id=api_id,
            api_hash=api_hash,
            bot_token=bot_token,
            max_concurrent_transmissions=max_concurrent_transmissions,
            db=db,
            lp=lp,
            free_daily_credits=free_daily_credits,
            admin_user_id=admin_user_id,
            apple_music_interfaces=apple_music_interfaces,
            apple_music_wrapper_interface=apple_music_wrapper_interface,
            credit_api_url=credit_api_url,
            kofi_verification_token=kofi_verification_token,
            kofi_shop_id=kofi_shop_id,
            kofi_url=kofi_url,
            user_locker=UserLocker(),
            upload_priority_semaphore=PrioritySemaphore(max_concurrent_transmissions),
            download_priority_semaphore=PrioritySemaphore(max_concurrent_transmissions),
            wrapper_locker=asyncio.Lock(),
            download_timeout=download_timeout,
            song_cache_chat_id=song_cache_chat_id,
            music_video_cache_chat_id=music_video_cache_chat_id,
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
        try:
            await bot.start()
            logger.info("Bot started")
            await idle()
        finally:
            await bot.stop()

    def get_lp(self, message: Message) -> Callable[..., str]:
        return lambda *path: self.lp.get(
            (message.from_user.language_code or "en").split("-")[0], *path
        )

    async def ensure_user_exists(self, message: Message) -> None:
        await self.db.user.add_if_not_exists(message.from_user.id)

    def is_admin(self, message: Message) -> bool:
        return message.from_user.id == self.admin_user_id

    async def add_free_daily_credits(self, message: Message) -> None:
        user = await self.db.user.get(message.from_user.id)
        if user is None:
            return

        now = datetime.datetime.now()
        if (
            user.last_free_credits_claim is None
            or (now - user.last_free_credits_claim).total_seconds() >= 86400
        ):
            await self.db.user.set_credits(
                user_id=user.id,
                credits=self.free_daily_credits,
            )
            await self.db.user.update_last_free_credits_claim(
                user_id=user.id,
                claim_time=now,
            )

    async def is_under_maintenance(self, message: Message) -> bool:
        lp = self.get_lp(message)

        lock_file = Path("lock")
        if lock_file.exists():
            await message.reply(lp("under_maintenance"))
            return True if message.from_user.id != self.admin_user_id else False
        return False
