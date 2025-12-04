import logging

from pyrogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
)

from ..bot import PinkMusicBot

logger = logging.getLogger(__name__)


def format_duration(seconds: int) -> str:
    minutes = seconds // 60
    seconds = seconds % 60
    return f"{minutes:02}:{seconds:02}"


async def get_song_search_results(
    search_results: list[dict],
    country_code: str,
    lp: callable,
):
    inline_results = []
    inline_results.append(
        InlineQueryResultArticle(
            title=lp("search_songs_header"),
            input_message_content=InputTextMessageContent(
                message_text=lp("search_songs_header")
            ),
        )
    )
    for result in search_results:
        song_id = result["id"]
        title = result["attributes"]["name"]
        artist = result["attributes"]["artistName"]
        duration = result["attributes"]["durationInMillis"] // 1000
        url = f"https://music.apple.com/{country_code.lower()}/song/{song_id}"
        thumb_url = result["attributes"]["artwork"]["url"].replace("{w}x{h}", "300x300")

        inline_results.append(
            InlineQueryResultArticle(
                title=title,
                input_message_content=InputTextMessageContent(message_text=url),
                description=lp("search_result_media").format(
                    artist=artist,
                    duration=format_duration(duration),
                ),
                thumb_url=thumb_url,
            )
        )
    if len(inline_results) == 1:
        inline_results.append(
            InlineQueryResultArticle(
                title=lp("search_no_results_title") + ".",
                input_message_content=InputTextMessageContent(
                    message_text=lp("search_no_results_description")
                ),
                description=lp("search_no_results_description"),
            )
        )
    return inline_results


async def get_music_video_search_results(
    search_results: list[dict],
    country_code: str,
    lp: callable,
):
    inline_results = []
    inline_results.append(
        InlineQueryResultArticle(
            title=lp("search_music_videos_header"),
            input_message_content=InputTextMessageContent(
                message_text=lp("search_music_videos_header")
            ),
        )
    )
    for result in search_results:
        song_id = result["id"]
        title = result["attributes"]["name"]
        artist = result["attributes"]["artistName"]
        duration = result["attributes"]["durationInMillis"] // 1000
        url = f"https://music.apple.com/{country_code.lower()}/music-video/{song_id}"
        thumb_url = result["attributes"]["artwork"]["url"].replace("{w}x{h}", "300x300")

        inline_results.append(
            InlineQueryResultArticle(
                title=title,
                input_message_content=InputTextMessageContent(message_text=url),
                description=lp("search_result_media").format(
                    artist=artist,
                    duration=format_duration(duration),
                ),
                thumb_url=thumb_url,
            )
        )
    if len(inline_results) == 1:
        inline_results.append(
            InlineQueryResultArticle(
                title=lp("search_no_results_title") + ".",
                input_message_content=InputTextMessageContent(
                    message_text=lp("search_no_results_description")
                ),
                description=lp("search_no_results_description"),
            )
        )
    return inline_results


async def get_album_search_results(
    search_results: list[dict],
    country_code: str,
    lp: callable,
):
    inline_results = []
    inline_results.append(
        InlineQueryResultArticle(
            title=lp("search_albums_header"),
            input_message_content=InputTextMessageContent(
                message_text=lp("search_albums_header")
            ),
        )
    )
    for result in search_results:
        album_id = result["id"]
        title = result["attributes"]["name"]
        artist = result["attributes"]["artistName"]
        year = result["attributes"].get("releaseDate", "1900")[:4]
        track_count = result["attributes"]["trackCount"]
        url = f"https://music.apple.com/{country_code.lower()}/album/{album_id}"
        thumb_url = result["attributes"]["artwork"]["url"].replace("{w}x{h}", "300x300")

        inline_results.append(
            InlineQueryResultArticle(
                title=title,
                input_message_content=InputTextMessageContent(message_text=url),
                description=lp("search_result_collection").format(
                    artist=artist,
                    year=year,
                    track_count=track_count,
                ),
                thumb_url=thumb_url,
            )
        )
    if len(inline_results) == 1:
        inline_results.append(
            InlineQueryResultArticle(
                title=lp("search_no_results_title") + ".",
                input_message_content=InputTextMessageContent(
                    message_text=lp("search_no_results_description")
                ),
                description=lp("search_no_results_description"),
            )
        )
    return inline_results


async def get_search_results(
    term: str, country_code: str, lp: callable, apple_music_interfaces: dict
):
    if not term:
        return [
            InlineQueryResultArticle(
                title=lp("search_empty_title"),
                input_message_content=InputTextMessageContent(
                    message_text=lp("search_empty_description")
                ),
                description=lp("search_empty_description"),
            )
        ]

    interface = apple_music_interfaces[country_code]
    apple_music_api = interface.apple_music_api
    search_results_response = await apple_music_api.get_search_results(
        term=term,
        types="songs,music-videos,albums",
        limit=15,
    )

    return [
        *await get_song_search_results(
            search_results=search_results_response["results"]
            .get("songs", {})
            .get("data", []),
            country_code=country_code,
            lp=lp,
        ),
        *await get_music_video_search_results(
            search_results=search_results_response["results"]
            .get("music-videos", {})
            .get("data", []),
            country_code=country_code,
            lp=lp,
        ),
        *await get_album_search_results(
            search_results=search_results_response["results"]
            .get("albums", {})
            .get("data", []),
            country_code=country_code,
            lp=lp,
        ),
    ]


@PinkMusicBot.on_inline_query()
async def inline_query_handler(bot: PinkMusicBot, inline_query: InlineQuery):
    await bot.ensure_user_exists(inline_query)
    lp = bot.get_lp(inline_query)
    user = await bot.db.user.get(inline_query.from_user.id)
    country_code = user.search_country
    if country_code.lower() not in bot.apple_music_interfaces:
        country_code = next(iter(bot.apple_music_interfaces.keys()))
        await bot.db.user.update_search_country(
            user_id=user.id,
            country_code=country_code,
        )
        await bot.send_message(
            chat_id=inline_query.from_user.id,
            text=lp("search_changed_auto").format(
                search_country=country_code,
            ),
        )

    try:
        results = await get_search_results(
            term=inline_query.query,
            country_code=country_code.lower(),
            lp=lp,
            apple_music_interfaces=bot.apple_music_interfaces,
        )
    except Exception:
        logger.exception(f"{inline_query.query}@{inline_query.from_user.id}")
        results = [
            InlineQueryResultArticle(
                title=lp("search_error_title"),
                input_message_content=InputTextMessageContent(
                    message_text=lp("search_error_description")
                ),
                description=lp("search_error_description"),
            )
        ]

    await inline_query.answer(
        results=results,
        cache_time=0,
    )
