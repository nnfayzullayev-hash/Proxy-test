import random

from database import db


async def generate_unique_code() -> str:
    while True:
        code = str(random.randint(100000, 999999))
        exists = await db.ticket_code_exists(code)
        if not exists:
            return code


async def create_manual_ticket(ticket_code, user_id, test_id):
    """Admin o'zi kod matnini kiritganda ishlatiladi."""
    return await db.create_ticket(ticket_code, user_id, test_id)


async def create_auto_ticket(user_id, test_id):
    """Bot avtomatik kod generatsiya qilganda ishlatiladi."""
    code = await generate_unique_code()
    ticket = await db.create_ticket(code, user_id, test_id)
    return ticket


async def validate_ticket_code(ticket_code):
    """Kodni tekshiradi. (ticket, error_message) qaytaradi."""
    ticket = await db.get_ticket_by_code(ticket_code.strip())
    if not ticket:
        return None, "❌ Bunday kod topilmadi."
    if ticket["status"] == "used":
        return None, "❌ Bu kod allaqachon ishlatilgan."
    return ticket, None
