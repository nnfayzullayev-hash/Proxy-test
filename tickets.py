from aiogram import Router, F
from aiogram.types import Message

from database import db

router = Router()


@router.message(F.text == "🎫 Chipta sotib olish")
async def buy_ticket_info(message: Message):
    settings = await db.get_settings()
    card = settings["card_number"] if settings and settings["card_number"] else "hali kiritilmagan"
    nickname = settings["nickname"] if settings and settings["nickname"] else "hali kiritilmagan"

    text = (
        "🎫 <b>Chipta sotib olish</b>\n\n"
        "To'lovni amalga oshirish uchun quyidagi karta raqamiga o'tkazma qiling "
        "va administrator bilan bog'lanib, kod (chipta) oling:\n\n"
        f"💳 Karta: <code>{card}</code>\n"
        f"👤 Admin: {nickname}"
    )
    await message.answer(text)
