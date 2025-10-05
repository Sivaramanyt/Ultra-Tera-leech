"""
Bot Core with Improved Conflict Handling
"""
import asyncio
import signal
import sys
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import Conflict, TimedOut, NetworkError
from telegram import Update
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
    
    # Add error handler that catches conflicts
    app.add_error_handler(_error_handler)
    
    logger.info(f"✅ Handlers ready for terabox_bot")

async def _error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle bot errors including conflicts"""
    error = context.error
    
    if isinstance(error, Conflict):
        logger.error(f"🔄 Conflict detected in error handler: {error}")
        # Force exit on conflict
        logger.info("⏳ Exiting due to conflict - Koyeb will restart")
        await asyncio.sleep(3)
        sys.exit(1)
    elif isinstance(error, (TimedOut, NetworkError)):
        logger.warning(f"Network error (will retry): {error}")
        return
    else:
        logger.error(f"Unexpected error: {error}")

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

class ConflictMonitor:
    """Monitor for conflict errors and restart if needed"""
    def __init__(self):
        self.conflict_count = 0
        self.last_conflict_time = 0
    
    def check_conflict(self, error_message):
        """Check if error indicates conflict"""
        if "Conflict" in str(error_message) or "terminated by other getUpdates" in str(error_message):
            import time
            current_time = time.time()
            
            if current_time - self.last_conflict_time < 30:  # Within 30 seconds
                self.conflict_count += 1
            else:
                self.conflict_count = 1
            
            self.last_conflict_time = current_time
            
            if self.conflict_count >= 3:  # 3 conflicts in 30 seconds
                logger.error("🔄 Multiple conflicts detected - restarting")
                return True
        return False

async def main():
    """Main bot function with enhanced conflict handling"""
    global should_stop
    
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    app = None
    health_runner = None
    conflict_monitor = ConflictMonitor()
    
    try:
        logger.info("🤖 Starting terabox_bot...")
        
        # Start health server for Koyeb
        health_runner = await start_health_server()
        
        # Create application with conflict handling
        app = Application.builder().token(config.BOT_TOKEN).build()
        
        # Setup handlers
        await _setup_handlers(app)
        
        # Clear updates
        await _clear_updates(app)
        
        # Start bot with custom updater settings
        logger.info("🚀 Starting Terabox Leech Bot...")
        
        await app.initialize()
        await app.start()
        
        # Custom polling with conflict detection
        updater = app.updater
        await updater.start_polling(
            drop_pending_updates=True,
            allowed_updates=['message', 'callback_query'],
            poll_interval=2.0,
            timeout=15,
            bootstrap_retries=1,  # Reduced retries
            read_timeout=10,
            write_timeout=10,
            connect_timeout=10,
            pool_timeout=10
        )
        
        logger.info("✅ Bot started successfully")
        
        # Monitor for conflicts
        conflict_check_interval = 0
        while not should_stop:
            await asyncio.sleep(1)
            conflict_check_interval += 1
            
            # Check for conflicts every 10 seconds
            if conflict_check_interval >= 10:
                try:
                    # Try a simple API call to detect conflicts
                    await app.bot.get_me()
                except Conflict as e:
                    logger.error(f"🔄 Conflict detected during monitoring: {e}")
                    break
                except Exception as e:
                    if conflict_monitor.check_conflict(str(e)):
                        break
                
                conflict_check_interval = 0
            
    except Conflict as e:
        logger.error(f"🔄 Conflict detected: {e}")
        logger.info("⏳ Waiting 30 seconds and restarting...")
        await asyncio.sleep(30)
        sys.exit(1)
        
    except Exception as e:
        logger.error(f"❌ Bot startup failed: {e}")
        if conflict_monitor.check_conflict(str(e)):
            logger.info("⏳ Conflict-like error detected - restarting...")
            await asyncio.sleep(30)
            sys.exit(1)
        else:
            sys.exit(1)
        
    finally:
        # Cleanup
        logger.info("🧹 Cleaning up...")
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
                
        logger.info("👋 Bot stopped - Koyeb will restart")
        sys.exit(1)  # Force restart

if __name__ == "__main__":
    asyncio.run(main())
    
