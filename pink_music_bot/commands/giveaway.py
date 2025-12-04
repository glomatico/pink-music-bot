import logging
from datetime import datetime, timedelta
from pathlib import Path

import httpx
from pyrogram import filters
from pyrogram.types import Message

from ..bot import PinkMusicBot

logger = logging.getLogger(__name__)


async def get_giveaway_codes(
    amount: int,
    months: int,
    credit_api_url: str,
    kofi_verification_token: str,
    kofi_shop_id: str,
) -> list[str] | None:
    async with httpx.AsyncClient() as http_client:
        try:
            response = await http_client.post(
                f"{credit_api_url}/giveaway",
                json={
                    "verification_token": kofi_verification_token,
                    "amount_credits": amount,
                    "shop_id": kofi_shop_id,
                    "amount": months,
                },
            )
            response.raise_for_status()
            data = response.json()
            return data["results"]
        except Exception:
            return None


@PinkMusicBot.on_message(
    filters.text & (filters.private | filters.group) & filters.command("giveaway")
)
async def message(bot: PinkMusicBot, message: Message):
    if not bot.is_admin(message):
        return
    lp = bot.get_lp(message)

    if len(message.command) < 3:
        await message.reply(lp("giveaway_invalid_arguments"))
        return

    amount_sr, months_str = message.command[1:3]
    try:
        amount = int(amount_sr)
        months = int(months_str)
    except ValueError:
        await message.reply(lp("giveaway_invalid_arguments"))
        return

    giveaway_codes = await get_giveaway_codes(
        amount,
        months,
        bot.credit_api_url,
        bot.kofi_verification_token,
        bot.kofi_shop_id,
    )
    if giveaway_codes is None:
        await message.reply(lp("giveaway_fail"))
        return

    await message.reply(
        lp("giveaway_success").format(
            amount=amount,
            months=months,
            codes="\n".join(
                [f"<code>/activate {code}</code>" for code in giveaway_codes]
            ),
        ),
        disable_web_page_preview=True,
    )
