from dataclasses import dataclass

import httpx
from pyrogram import filters
from pyrogram.types import Message

from ..bot import PinkMusicBot


@dataclass
class ActivationResult:
    days: int
    email: str


async def validate_activation_code(
    credit_id: str,
    credit_api_url: str,
    kofi_verification_token: str,
) -> ActivationResult | None:
    async with httpx.AsyncClient() as http_client:
        try:
            response = await http_client.post(
                f"{credit_api_url}/reedem",
                json={
                    "credit_id": credit_id,
                    "verification_token": kofi_verification_token,
                },
            )
            response.raise_for_status()
            data = response.json()
            return ActivationResult(
                days=data["amount"] * 31,
                email=data["email"],
            )
        except Exception:
            return None


@PinkMusicBot.on_message(
    filters.text & (filters.private | filters.group) & filters.command("activate")
)
async def message(bot: PinkMusicBot, message: Message):
    await bot.ensure_user_exists(message)
    lp = bot.get_lp(message)

    if not message.command[1:]:
        await message.reply(lp("activate_no_code"))
        return
    code = message.command[1]

    activation_result = await validate_activation_code(
        credit_id=code,
        credit_api_url=bot.credit_api_url,
        kofi_verification_token=bot.kofi_verification_token,
    )
    if activation_result is None:
        await message.reply(lp("activate_invalid_code"))
        return

    user = await bot.db.user.get(message.from_user.id)
    membership_due_data = await bot.db.user.add_membership_days(
        user.id,
        activation_result.days,
        activation_result.email if activation_result.email != "giveaway" else None,
    )

    await message.reply(
        lp("activate_success").format(
            membership_due_date=membership_due_data.strftime("%Y-%m-%d"),
        ),
        disable_web_page_preview=True,
    )
