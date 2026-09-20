from datetime import datetime
import pytz

from database import db


async def create_test(name, description, pdf_file_id):
    return await db.create_test(name, description, pdf_file_id)


async def set_test_time(test_id, start_time):
    return await db.set_test_time(test_id, start_time)


async def get_test(test_id):
    return await db.get_test(test_id)


async def list_tests():
    return await db.list_tests()


def is_test_ready(test):
    """Test hozir topshirish uchun tayyor-tayyormasligini tekshiradi."""
    
    # Agar status "draft" bo'lsa
    if test["status"] == "draft":
        return False, "❌ Bu test hali tayyor emas. Admin tarafidan tayyorlanishini kuting."
    
    # Agar vaqt belgilanmagan bo'lsa
    if not test["start_time"]:
        return False, "❌ Bu test uchun vaqt belgilanmagan. Admin bilan bog'laning."
    
    # Uzbek vaqti (UTC+5)
    tashkent_tz = pytz.timezone('Asia/Tashkent')
    now = datetime.now(tashkent_tz)
    
    # Start time'ni Tashkent vaqtiga o'tkazish
    start_time = test["start_time"]
    
    # Agar start_time naive (timezone yo'q) bo'lsa, UTC deb qabul qilip Tashkent'ga o'tkazamiz
    if start_time.tzinfo is None:
        start_time_utc = pytz.UTC.localize(start_time)
        start_time = start_time_utc.astimezone(tashkent_tz)
    else:
        start_time = start_time.astimezone(tashkent_tz)
    
    # Vaqt hali keliniga qolgan bo'lsa
    if now < start_time:
        time_remaining = start_time - now
        hours = int(time_remaining.total_seconds() // 3600)
        minutes = int((time_remaining.total_seconds() % 3600) // 60)
        
        if hours > 0:
            return False, f"⏳ Test hali boshlanmagan.\nBoshlanish vaqti: {start_time.strftime('%d.%m.%Y %H:%M')}\nQolgan vaqt: {hours} soat {minutes} minut"
        else:
            return False, f"⏳ Test hali boshlanmagan.\nBoshlanish vaqti: {start_time.strftime('%d.%m.%Y %H:%M')}\nQolgan vaqt: {minutes} minut"
    
    return True, ""
    
