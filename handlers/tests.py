from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message

from database import db
import config
from services import ticket_service, test_service

router = Router()


class TakeTest(StatesGroup):
    entering_code = State()
    waiting_answer = State()


@router.message(F.text == "📝 Testlar")
async def ask_ticket_code(message: Message, state: FSMContext):
    await message.answer("Chipta (kod)ingizni kiriting:")
    await state.set_state(TakeTest.entering_code)


@router.message(TakeTest.entering_code)
async def code_entered(message: Message, state: FSMContext, bot):
    ticket, error = await ticket_service.validate_ticket_code(message.text)
    if error:
        await message.answer(error)
        await state.clear()
        return

    test = await test_service.get_test(ticket["test_id"])
    ready, err_msg = test_service.is_test_ready(test)
    if not ready:
        await message.answer(f"❌ {err_msg}")
        await state.clear()
        return

    if not test["pdf_file_id"]:
        await message.answer("❌ Bu test uchun hali fayl yuklanmagan. Admin bilan bog'laning.")
        await state.clear()
        return

    await db.mark_ticket_used(ticket["id"])

    await state.update_data(
        test_id=test["id"],
        test_name=test["name"],
        ticket_id=ticket["id"],
        ticket_code=ticket["ticket_code"],
    )

    await bot.send_document(
        message.chat.id,
        test["pdf_file_id"],
        caption=(
            f"📝 {test['name']}\n\n"
            "Testni yeching. Yechib bo'lgach, javobingizni istalgan ko'rinishda "
            "(rasm, hujjat yoki matn) shu yerga yuboring."
        ),
    )
    await state.set_state(TakeTest.waiting_answer)


@router.message(TakeTest.waiting_answer)
async def answer_received(message: Message, state: FSMContext, bot):
    data = await state.get_data()
    user = await db.get_user_by_telegram_id(message.from_user.id)

    content_type = message.content_type
    file_id = None
    text_content = None

    if message.photo:
        file_id = message.photo[-1].file_id
    elif message.document:
        file_id = message.document.file_id
    elif message.video:
        file_id = message.video.file_id
    elif message.voice:
        file_id = message.voice.file_id
    elif message.audio:
        file_id = message.audio.file_id
    elif message.animation:
        file_id = message.animation.file_id
    elif message.text:
        text_content = message.text

    await db.create_submission(
        user["id"], data["test_id"], data["ticket_id"], content_type, file_id, text_content
    )

    caption = (
        f"📥 Yangi javob\n\n"
        f"Foydalanuvchi: {message.from_user.full_name} (@{message.from_user.username or '-'})\n"
        f"Test: {data['test_name']}\n"
        f"Chipta: {data['ticket_code']}"
    )
    for admin_id in config.ADMIN_IDS:
        try:
            await bot.send_message(admin_id, caption)
            await bot.forward_message(admin_id, message.chat.id, message.message_id)
        except Exception:
            pass

    await message.answer("✅ Javobingiz qabul qilindi, rahmat!")
    await state.clear()
