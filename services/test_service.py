from datetime import datetime

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
    if test["status"] != "active" or not test["start_time"]:
        return False, "Bu test uchun hali vaqt belgilanmagan."
    if datetime.now() < test["start_time"]:
        return False, f"Test hali boshlanmagan. Boshlanish vaqti: {test['start_time'].strftime('%d.%m.%Y %H:%M')}"
    return True, ""
