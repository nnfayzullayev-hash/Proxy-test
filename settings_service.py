from database import db


async def get_settings():
    return await db.get_settings()


async def set_card_number(value):
    await db.set_card_number(value)


async def set_nickname(value):
    await db.set_nickname(value)
