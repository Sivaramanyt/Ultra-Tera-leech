"""
Fixed Bot Core - Health Check + Event Loop Safe
"""
import asyncio
import signal
import sys
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from telegram.error import Conflict, TimedOut, NetworkError
from loguru import logger
import config

# Global variable to handle graceful shutdown
should_stop = False

def signal_handler(signum, frame):
    """Handle shutdown signals"""
    global should_stop
    should_stop = True
    logger.info("🛑 Shutdown signal received")

async def _setup_handlers(app):
    """Setup all bot handlers"""
    from bot.handlers import BotHandlers
    handlers = BotHandlers()
    
    # Command handlers
    app.add_handler(CommandHandler("start", handlers.start_command))
    app.add_handler(CommandHandler("help", handlers.help_command))
    app.add_handler(CommandHandler("cancel", handlers.cancel_command))
    app.add_handler(CommandHandler("stats", handlers.stats_command))
    
    # Terabox link handler
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & filters.Regex(
            r'https?://.*(terabox|1024terabox|teraboxurl|mirrobox|nephobox|4funbox)\.com'
        ),
        handlers.handle_terabox_link
    ))
    
    # Text handler
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handlers.handle_text
    ))
    
    logger.info(f"✅ Handlers ready for terabox_bot")

async def _clear_updates(app):
    """Clear webhook and pending updates"""
    try:
        await app.bot.delete_webhook(drop_pending_updates=True)
        logger.info("🧹 Cleared webhook and pending updates")
    except Exception as e:
        logger.warning(f"Could not clear updates: {e}")

async def start_health_server():
    """Start simple HTTP health server for Koyeb"""
    from aiohttp import web
    
    async def health_check(request):
        return web.Response(text="Bot is healthy", status=200)
    
    app = web.Application()
    app.router.add_get('/health', health_check)
    app.router.add_get('/', health_check)
    
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8000)
    await site.start()
    logger.info("🏥 Health server started on port 8000")
    return runner

async def main():
    """Main bot function - Simple and Reliable"""
    global should_stop
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    app = None
    health_runner = None
    
    try:
        logger.info("🤖 Starting terabox_bot...")
        
        # Start health server for Koyeb
        health_runner = await start_health_server()
        
        # Create application
        app = Application.builder().token(config.BOT_TOKEN).build()
        
        # Setup handlers
        await _setup_handlers(app)
        
        # Clear updates
        await _clear_updates(app)
        
        # Start bot with conflict handling
        logger.info("🚀 Starting Terabox Leech Bot...")
        
        # Configure polling with conflict resistance
        await app.initialize()
        await app.start()
        await app.updater.start_polling(
            drop_pending_updates=True,
            allowed_updates=['message', 'callback_query'],
            poll_interval=1.0,
            timeout=20,
            bootstrap_retries=3,
            read_timeout=10,
            write_timeout=10,
            connect_timeout=10,
            pool_timeout=10
        )
        
        logger.info("✅ Bot started successfully")
        
        # Keep running until signal received
        while not should_stop:
            await asyncio.sleep(1)
            
    except Conflict as e:
        logger.error(f"🔄 Conflict detected: {e}")
        logger.info("⏳ Waiting 30 seconds and restarting...")
        await asyncio.sleep(30)
        # Exit and let Koyeb restart
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"❌ Bot startup failed: {e}")
        sys.exit(1)
        
    finally:
        # Cleanup
        if app:
            try:
                await app.updater.stop()
                await app.stop()
                await app.shutdown()
            except:
                pass
                
        if health_runner:
            try:
                await health_runner.cleanup()
            except:
                pass
                
        logger.info("👋 Bot stopped")

if __name__ == "__main__":
    asyncio.run(main())
    
