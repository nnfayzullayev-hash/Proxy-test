import asyncio
import logging
import os
import signal

from aiohttp import web
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage

import config
from database import db
from handlers import start, news, tickets, tests, admin

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def handle_ping(request):
    """Keep-alive veb-server"""
    return web.Response(text="Bot ishlab turibdi ✅")


async def start_web_server():
    """Keep-alive veb-server"""
    app = web.Application()
    app.router.add_get("/", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 10000))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    logger.info(f"🌐 Keep-alive server {port}-portda ishga tushdi")
    return runner


async def main():
    logger.info("🤖 Bot ishga tushish boshlandi...")
    
    # Database ulaning
    try:
        await db.connect()
        logger.info("✅ Database ulanish muvaffaqiyatli")
    except Exception as e:
        logger.error(f"❌ Database ulanib bo'lmadi: {e}")
        return

    # Bot va Dispatcher sozlash
    bot = Bot(token=config.BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
    dp = Dispatcher(storage=MemoryStorage())

    # Handler'larni ro'yxatga qo'shish
    dp.include_router(admin.router)
    dp.include_router(tickets.router)
    dp.include_router(tests.router)
    dp.include_router(news.router)
    dp.include_router(start.router)

    # Webhook tozalash - MUHIM!
    try:
        webhook_info = await bot.get_webhook_info()
        if webhook_info.url:
            logger.info(f"⚠️ WebHook hali aktiv: {webhook_info.url}")
            await bot.delete_webhook(drop_pending_updates=True)
            logger.info("✅ WebHook tozalandi")
    except Exception as e:
        logger.warning(f"WebHook tekshirishda xato: {e}")
    
    # Keep-alive server ishga tushirish
    web_runner = None
    try:
        web_runner = await start_web_server()
    except Exception as e:
        logger.warning(f"Keep-alive server ishga tushmadi: {e}")

    try:
        logger.info("📡 Bot polling boshlanmoqda...")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        logger.error(f"❌ Bot xatosi: {e}")
    finally:
        await db.close()
        await bot.session.close()
        if web_runner:
            await web_runner.cleanup()
        logger.info("✅ Bot yopildi")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("⚠️ Bot qo'lma to'xtatildi")
    except Exception as e:
        logger.error(f"❌ Kritik xato: {e}")
