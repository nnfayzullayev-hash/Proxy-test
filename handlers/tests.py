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

    # Test tayyor bo'lgan bo'lmi
    ready, err_msg = test_service.is_test_ready(test)
    if not ready:
        await message.answer(err_msg)
        await state.clear()
        return

    # PDF file_id bor-yo'q
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
            document=test["pdf_file_id"],
            caption=f"📝 <b>{test['name']}</b>"
        )
        
        logger.info("PDF muvaffaqiyatli yuborildi")
        
    except Exception as e:
        logger.error(f"PDF yuborib bo'lmadi: {e}", exc_info=True)
        await message.answer(f"❌ PDF yuborib bo'lmadi. Xato: {str(e)}")
        await state.clear()
        return

    # Namuna ko'rsatish
    await message.answer(
        "📌 <b>Javoblarni quyidagi formatda kiritish:</b>\n\n"
        "1A\n"
        "2B\n"
        "3D\n"
        "4C\n"
        "5A\n"
        "...\n\n"
        "Barchasini kiritganingizdan keyin yuboring ✅"
    )
    
    await state.set_state(TakeTest.waiting_answer)


@router.message(TakeTest.waiting_answer)
async def answer_received(message: Message, state: FSMContext):
    data = await state.get_data()
    user = await db.get_user_by_telegram_id(message.from_user.id)

    if not user:
        await message.answer("❌ Foydalanuvchi topilmadi")
        await state.clear()
        return

    # Javobni matn sifatida qabul qilish
    text_content = message.text.strip()
    
    if not text_content:
        await message.answer("❌ Javob kiritingiz")
        return

    # Javobni bazaga saqlash
    try:
        submission = await db.create_submission(
            user["id"], 
            data["test_id"], 
            data["ticket_id"], 
            "text",  # Har doim matn formatida
            None,  # file_id yo'q
            text_content  # Javob matni
        )
        logger.info(f"Javob saqlandi. Submission ID: {submission['id']}")
    except Exception as e:
        logger.error(f"Javob saqlana olmadi: {e}")
        await message.answer(f"❌ Javob saqlana olmadi: {e}")
        await state.clear()
        return

    # Admin'larga xabar
    try:
        for admin_id in config.ADMIN_IDS:
            admin_msg = (
                f"📬 <b>Yangi javob keldi!</b>\n\n"
                f"👤 Foydalanuvchi ID: {user['id']}\n"
                f"📝 Test: {data['test_name']}\n"
                f"🎫 Kod: {data['ticket_code']}\n\n"
                f"<b>Javoblar:</b>\n{text_content}"
            )
            await message.bot.send_message(admin_id, admin_msg)
    except Exception as e:
        logger.warning(f"Admin'ga xabar yuborib bo'lmadi: {e}")

    await message.answer("✅ Javobingiz qabul qilindi, rahmat!")
    await state.clear()
