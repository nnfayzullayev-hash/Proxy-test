from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton

from database import db
import config

router = Router()


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text="📰 Yangiliklar")],
        [KeyboardButton(text="🎫 Chipta sotib olish")],
        [KeyboardButton(text="📝 Testlar")],
    ], resize_keyboard=True)


@router.message(CommandStart())
async def cmd_start(message: Message):
    user = message.from_user
    await db.get_or_create_user(user.id, user.first_name, user.last_name, user.username)

    text = f"Assalomu alaykum, {user.first_name}! 👋\n\nQuyidagi menyudan foydalaning:"
    if user.id in config.ADMIN_IDS:
        text += (
            "\n\n👨‍💼 Siz adminsiz. Admin buyruqlari:\n"
            "/addnews — yangilik qo'shish\n"
            "/delnews — yangilik o'chirish\n"
            "/addtests — test qo'shish (PDF)\n"
            "/addtesttime — testga vaqt belgilash\n"
            "/addtickets — foydalanuvchiga qo'lda kod berish\n"
            "/addusers — foydalanuvchiga avtomatik kod berish\n"
            "/addcardnumber — to'lov karta raqamini o'zgartirish\n"
            "/addnickname — to'lov uchun nikni o'zgartirish\n"
            "/javoblar — kelgan javoblar ro'yxati"
        )

    await message.answer(text, reply_markup=main_menu_keyboard())
