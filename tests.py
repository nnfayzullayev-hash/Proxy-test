from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import Message
import logging

from database import db
import config
from services import ticket_service, test_service

router = Router()
logger = logging.getLogger(__name__)


class TakeTest(StatesGroup):
    entering_code = State()
    waiting_answer = State()


@router.message(F.text == "📝 Testlar")
async def ask_ticket_code(message: Message, state: FSMContext):
    await message.answer("Chipta (kod)ingizni kiriting:")
    await state.set_state(TakeTest.entering_code)


@router.message(TakeTest.entering_code)
async def code_entered(message: Message, state: FSMContext):
    code = message.text.strip()
    
    # Kodni tekshirish
    ticket, error = await ticket_service.validate_ticket_code(code)
    if error:
        await message.answer(error)
        await state.clear()
        return

    # Test'ni olish
    test = await test_service.get_test(ticket["test_id"])
    if not test:
        await message.answer("❌ Test topilmadi")
        await state.clear()
        return

    logger.info(f"Test: {test['name']}, Status: {test['status']}, Start time: {test['start_time']}, PDF: {test['pdf_file_id']}")

    # Test tayyor bo'lgan bo'lmi tekshirish
    ready, err_msg = test_service.is_test_ready(test)
    if not ready:
        await message.answer(err_msg)
        await state.clear()
        return

    # PDF file_id bor-yo'qligini tekshirish
    if not test["pdf_file_id"]:
        await message.answer("❌ Bu test uchun hali PDF fayl yuklanmagan. Admin bilan bog'laning.")
        await state.clear()
        return

    # Kodni "used" qilish
    try:
        await db.mark_ticket_used(ticket["id"])
    except Exception as e:
        logger.error(f"Kod belgilashda xato: {e}")
        await message.answer(f"❌ Texnik xato: {e}")
        await state.clear()
        return

    # State'ga ma'lumot saqlash
    await state.update_data(
        test_id=test["id"],
        test_name=test["name"],
        ticket_id=ticket["id"],
        ticket_code=ticket["ticket_code"],
    )

    # PDF testni yuborish
    try:
        logger.info(f"PDF yuborilmoqda. File ID: {test['pdf_file_id']}")
        await message.answer_document(
            test["pdf_file_id"],
            caption=(
                f"📝 <b>{test['name']}</b>\n\n"
                "Testni yeching. Yechib bo'lgach, javobingizni istalgan ko'rinishda "
                "(rasm, hujjat, matn, video) shu yerga yuboring."
            ),
        )
        logger.info("PDF muvaffaqiyatli yuborildi")
    except Exception as e:
        logger.error(f"PDF yuborib bo'lmadi: {e}")
        await message.answer(f"❌ PDF yuborib bo'lmadi. Xato: {str(e)}\n\nAdmin bilan bog'laning.")
        await state.clear()
        return

    await state.set_state(TakeTest.waiting_answer)


@router.message(TakeTest.waiting_answer)
async def answer_received(message: Message, state: FSMContext):
    data = await state.get_data()
    user = await db.get_user_by_telegram_id(message.from_user.id)

    if not user:
        await message.answer("❌ Foydalanuvchi topilmadi")
        await state.clear()
        return

    content_type = message.content_type
    file_id = None
    text_content = None

    # Turli xil format'larni qabul qilish
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
    else:
        await message.answer("❌ Noto'g'ri format. Rasm, hujjat, video, ovoz yoki matn yuboring.")
        return

    # Javobni bazaga saqlash
    try:
        submission = await db.create_submission(
            user["id"], data["test_id"], data["ticket_id"], content_type, file_id, text_content
        )
        logger.info(f"Javob saqlandi. Submission ID: {submission['id']}")
    except Exception as e:
        logger.error(f"Javob saqlana olmadi: {e}")
        await message.answer(f"❌ Javob saqlana olmadi: {e}")
        await state.clear()
        return

    await message.answer("✅ Javobingiz qabul qilindi, rahmat! Admin javobingizni ko'radi.")
    await state.clear()
