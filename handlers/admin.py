from datetime import datetime

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import (
    Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton
)

from database import db
import config
from services import ticket_service, test_service, settings_service

router = Router()


def is_admin(user_id: int) -> bool:
    return user_id in config.ADMIN_IDS


async def build_tests_keyboard(prefix: str):
    tests = await test_service.list_tests()
    if not tests:
        return None
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"{t['name']} (#{t['id']})", callback_data=f"{prefix}:{t['id']}")]
        for t in tests
    ])


# ---------------- YANGILIK QO'SHISH / O'CHIRISH ----------------

class AddNews(StatesGroup):
    title = State()
    text = State()


@router.message(Command("addnews"))
async def add_news_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await message.answer("Yangilik sarlavhasini kiriting:")
    await state.set_state(AddNews.title)


@router.message(AddNews.title)
async def add_news_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text)
    await message.answer("Yangilik matnini kiriting:")
    await state.set_state(AddNews.text)


@router.message(AddNews.text)
async def add_news_text(message: Message, state: FSMContext):
    data = await state.get_data()
    await db.add_news(data["title"], message.text)
    await message.answer("✅ Yangilik qo'shildi.")
    await state.clear()


@router.message(Command("delnews"))
async def del_news_list(message: Message):
    if not is_admin(message.from_user.id):
        return
    news_list = await db.get_news_list(limit=15)
    if not news_list:
        await message.answer("Yangiliklar mavjud emas.")
        return
    for item in news_list:
        kb = InlineKeyboardMarkup(inline_keyboard=[[
            InlineKeyboardButton(text="🗑 O'chirish", callback_data=f"delnews:{item['id']}")
        ]])
        await message.answer(f"📰 {item['title']}", reply_markup=kb)


@router.callback_query(F.data.startswith("delnews:"))
async def del_news_confirm(callback: CallbackQuery):
    if not is_admin(callback.from_user.id):
        await callback.answer()
        return
    news_id = int(callback.data.split(":")[1])
    await db.delete_news(news_id)
    await callback.answer("O'chirildi.")
    await callback.message.delete()


# ---------------- TEST QO'SHISH (PDF) ----------------

class AddTest(StatesGroup):
    name = State()
    description = State()
    pdf = State()


@router.message(Command("addtests"))
async def add_test_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await message.answer("Test nomini kiriting:")
    await state.set_state(AddTest.name)


@router.message(AddTest.name)
async def add_test_name(message: Message, state: FSMContext):
    await state.update_data(name=message.text)
    await message.answer("Test haqida qisqacha ma'lumot kiriting:")
    await state.set_state(AddTest.description)


@router.message(AddTest.description)
async def add_test_description(message: Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer("Endi test faylini (PDF) yuboring:")
    await state.set_state(AddTest.pdf)


@router.message(AddTest.pdf, F.document)
async def add_test_pdf(message: Message, state: FSMContext):
    data = await state.get_data()
    test = await test_service.create_test(data["name"], data["description"], message.document.file_id)
    await message.answer(
        f"✅ Test yaratildi: {test['name']} (#{test['id']})\n\n"
        f"Endi /addtesttime orqali unga vaqt belgilang."
    )
    await state.clear()


@router.message(AddTest.pdf)
async def add_test_pdf_wrong(message: Message):
    await message.answer("Iltimos, PDF faylni hujjat (document) sifatida yuboring.")


# ---------------- TESTGA VAQT BELGILASH ----------------

class SetTestTime(StatesGroup):
    choosing_test = State()
    entering_time = State()


@router.message(Command("addtesttime"))
async def set_test_time_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    kb = await build_tests_keyboard("settime")
    if not kb:
        await message.answer("Hozircha testlar mavjud emas. Avval /addtests orqali qo'shing.")
        return
    await message.answer("Qaysi testga vaqt belgilaymiz?", reply_markup=kb)
    await state.set_state(SetTestTime.choosing_test)


@router.callback_query(SetTestTime.choosing_test, F.data.startswith("settime:"))
async def set_test_time_chosen(callback: CallbackQuery, state: FSMContext):
    test_id = int(callback.data.split(":")[1])
    await state.update_data(test_id=test_id)
    await callback.message.answer("Boshlanish sanasi va vaqtini kiriting (masalan: 30.08.2026 15:00):")
    await state.set_state(SetTestTime.entering_time)
    await callback.answer()


@router.message(SetTestTime.entering_time)
async def set_test_time_entered(message: Message, state: FSMContext):
    try:
        dt = datetime.strptime(message.text.strip(), "%d.%m.%Y %H:%M")
    except ValueError:
        await message.answer("❌ Noto'g'ri format. Masalan: 30.08.2026 15:00")
        return
    data = await state.get_data()
    test = await test_service.set_test_time(data["test_id"], dt)
    await message.answer(f"✅ \"{test['name']}\" uchun vaqt belgilandi: {dt.strftime('%d.%m.%Y %H:%M')}")
    await state.clear()


# ---------------- FOYDALANUVCHIGA QO'LDA KOD BERISH ----------------

class AddTicketManual(StatesGroup):
    choosing_test = State()
    entering_telegram_id = State()
    entering_code = State()


@router.message(Command("addtickets"))
async def add_ticket_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    kb = await build_tests_keyboard("mticket")
    if not kb:
        await message.answer("Hozircha testlar mavjud emas. Avval /addtests orqali qo'shing.")
        return
    await message.answer("Qaysi test uchun kod berasiz?", reply_markup=kb)
    await state.set_state(AddTicketManual.choosing_test)


@router.callback_query(AddTicketManual.choosing_test, F.data.startswith("mticket:"))
async def add_ticket_test_chosen(callback: CallbackQuery, state: FSMContext):
    test_id = int(callback.data.split(":")[1])
    await state.update_data(test_id=test_id)
    await callback.message.answer("Foydalanuvchining Telegram ID raqamini kiriting:")
    await state.set_state(AddTicketManual.entering_telegram_id)
    await callback.answer()


@router.message(AddTicketManual.entering_telegram_id)
async def add_ticket_telegram_id(message: Message, state: FSMContext):
    if not message.text.strip().lstrip("-").isdigit():
        await message.answer("❌ Faqat raqam kiriting.")
        return
    target_id = int(message.text.strip())
    user = await db.get_user_by_telegram_id(target_id)
    if not user:
        await message.answer(
            "❌ Bu foydalanuvchi topilmadi — u hali botga /start yozmagan bo'lishi mumkin."
        )
        await state.clear()
        return
    await state.update_data(target_telegram_id=target_id, target_user_id=user["id"])
    await message.answer("Endi shu foydalanuvchi uchun kod (masalan: ABC123) kiriting:")
    await state.set_state(AddTicketManual.entering_code)


@router.message(AddTicketManual.entering_code)
async def add_ticket_code_entered(message: Message, state: FSMContext, bot):
    code = message.text.strip()
    exists = await db.ticket_code_exists(code)
    if exists:
        await message.answer("❌ Bu kod allaqachon band. Boshqa kod kiriting.")
        return

    data = await state.get_data()
    await ticket_service.create_manual_ticket(code, data["target_user_id"], data["test_id"])
    test = await test_service.get_test(data["test_id"])

    try:
        await bot.send_message(
            data["target_telegram_id"],
            f"🎫 Sizga chipta berildi!\n\nTest: {test['name']}\nKod: <code>{code}</code>",
            parse_mode="HTML",
        )
        await message.answer(f"✅ Kod \"{code}\" foydalanuvchiga yuborildi.")
    except Exception:
        await message.answer(
            f"⚠️ Kod bazaga saqlandi (\"{code}\"), lekin foydalanuvchiga xabar yuborib bo'lmadi "
            "(botni bloklagan yoki hali /start bosmagan bo'lishi mumkin)."
        )
    await state.clear()


# ---------------- FOYDALANUVCHIGA AVTOMATIK KOD BERISH ----------------

class AddUserAuto(StatesGroup):
    choosing_test = State()
    entering_telegram_id = State()


@router.message(Command("addusers"))
async def add_user_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    kb = await build_tests_keyboard("auser")
    if not kb:
        await message.answer("Hozircha testlar mavjud emas. Avval /addtests orqali qo'shing.")
        return
    await message.answer("Qaysi test uchun foydalanuvchi qo'shamiz?", reply_markup=kb)
    await state.set_state(AddUserAuto.choosing_test)


@router.callback_query(AddUserAuto.choosing_test, F.data.startswith("auser:"))
async def add_user_test_chosen(callback: CallbackQuery, state: FSMContext):
    test_id = int(callback.data.split(":")[1])
    await state.update_data(test_id=test_id)
    await callback.message.answer("Foydalanuvchining Telegram ID raqamini kiriting:")
    await state.set_state(AddUserAuto.entering_telegram_id)
    await callback.answer()


@router.message(AddUserAuto.entering_telegram_id)
async def add_user_telegram_id(message: Message, state: FSMContext, bot):
    if not message.text.strip().lstrip("-").isdigit():
        await message.answer("❌ Faqat raqam kiriting.")
        return
    target_id = int(message.text.strip())
    user = await db.get_user_by_telegram_id(target_id)
    if not user:
        await message.answer(
            "❌ Bu foydalanuvchi topilmadi — u hali botga /start yozmagan bo'lishi mumkin."
        )
        await state.clear()
        return

    data = await state.get_data()
    ticket = await ticket_service.create_auto_ticket(user["id"], data["test_id"])
    test = await test_service.get_test(data["test_id"])

    try:
        await bot.send_message(
            target_id,
            f"🎫 Sizga chipta berildi!\n\nTest: {test['name']}\nKod: <code>{ticket['ticket_code']}</code>",
            parse_mode="HTML",
        )
        await message.answer(f"✅ Kod \"{ticket['ticket_code']}\" yaratildi va foydalanuvchiga yuborildi.")
    except Exception:
        await message.answer(
            f"⚠️ Kod \"{ticket['ticket_code']}\" yaratildi, lekin foydalanuvchiga xabar yuborib bo'lmadi."
        )
    await state.clear()


# ---------------- KARTA RAQAM VA NIK ----------------

class SetCard(StatesGroup):
    value = State()


@router.message(Command("addcardnumber"))
async def set_card_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await message.answer("Yangi karta raqamini kiriting:")
    await state.set_state(SetCard.value)


@router.message(SetCard.value)
async def set_card_value(message: Message, state: FSMContext):
    await settings_service.set_card_number(message.text.strip())
    await message.answer("✅ Karta raqami yangilandi.")
    await state.clear()


class SetNickname(StatesGroup):
    value = State()


@router.message(Command("addnickname"))
async def set_nickname_start(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return
    await message.answer("Yangi nikni kiriting (masalan: @username):")
    await state.set_state(SetNickname.value)


@router.message(SetNickname.value)
async def set_nickname_value(message: Message, state: FSMContext):
    await settings_service.set_nickname(message.text.strip())
    await message.answer("✅ Nik yangilandi.")
    await state.clear()


# ---------------- JAVOBLAR RO'YXATI ----------------

@router.message(Command("javoblar"))
async def list_submissions(message: Message):
    if not is_admin(message.from_user.id):
        return
    submissions = await db.list_submissions(limit=20)
    if not submissions:
        await message.answer("Hozircha javoblar yo'q.")
        return
    lines = []
    for s in submissions:
        test = await db.get_test(s["test_id"])
        user = await db.get_user_by_id(s["user_id"])
        lines.append(
            f"🕓 {s['created_at'].strftime('%d.%m.%Y %H:%M')} | "
            f"{user['first_name'] if user else '-'} | "
            f"{test['name'] if test else '-'} | {s['content_type']}"
        )
    await message.answer("\n".join(lines))
