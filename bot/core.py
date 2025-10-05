"""
Bot core with automatic conflict resolution - Complete File
"""
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import Conflict, TimedOut, NetworkError
from loguru import logger
import config

class TeraboxBot:
    def __init__(self):
        self.app = None
        self.max_retries = 10
        self.base_delay = 5
    
    async def _setup_handlers(self):
        """Setup all bot handlers"""
        from .handlers import BotHandlers
        handlers = BotHandlers()
        
        # Command handlers
        self.app.add_handler(CommandHandler("start", handlers.start_command))
        self.app.add_handler(CommandHandler("help", handlers.help_command))
        self.app.add_handler(CommandHandler("cancel", handlers.cancel_command))
        self.app.add_handler(CommandHandler("stats", handlers.stats_command))
        
        # Message handlers
        self.app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND & filters.Regex(
                r'https?://.*(terabox|1024terabox|teraboxurl|mirrobox|nephobox|4funbox)\.com'
            ),
            handlers.handle_terabox_link
        ))
        
        self.app.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handlers.handle_text
        ))
        
        # Error handler
        self.app.add_error_handler(self._error_handler)
        
        logger.info(f"✅ Handlers ready for {self.app.bot.username}")
    
    async def _error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle bot errors with conflict resolution"""
        error = context.error
        
        if isinstance(error, Conflict):
            logger.error(f"Bot error: {error}")
            logger.warning("Conflict detected - another bot instance may be running")
            # Don't restart here, let the main loop handle it
            return
        elif isinstance(error, (TimedOut, NetworkError)):
            logger.warning(f"Network error (will retry): {error}")
            return
        else:
            logger.error(f"Unexpected error: {error}")
    
    async def run(self):
        """Run bot with automatic conflict handling"""
        logger.info(f"🤖 Starting {config.BOT_TOKEN[:10]}...")
        
        for attempt in range(self.max_retries):
            try:
                # Setup application
                await self._setup_application()
                
                # Clear any existing webhooks/updates
                await self._clear_updates()
                
                # Start polling with conflict handling
                logger.info("🚀 Starting polling with conflict protection...")
                await self.app.run_polling(
                    drop_pending_updates=True,
                    close_loop=False,
                    stop_signals=None,
                    poll_interval=2.0,
                    timeout=20,
                    bootstrap_retries=3,
                    read_timeout=10,
                    write_timeout=10,
                    connect_timeout=10,
                    pool_timeout=10
                )
                return  # Success
                
            except Conflict as e:
                logger.warning(f"🔄 Conflict on attempt {attempt + 1}: {e}")
                await self._handle_conflict(attempt + 1)
                
            except Exception as e:
                logger.error(f"❌ Error on attempt {attempt + 1}: {e}")
                if attempt < self.max_retries - 1:
                    wait_time = self.base_delay * (2 ** attempt)  # Exponential backoff
                    logger.info(f"⏳ Retrying in {wait_time} seconds...")
                    await asyncio.sleep(wait_time)
                else:
                    logger.error("❌ Max retries reached")
                    raise
    
    async def _setup_application(self):
        """Setup fresh application"""
        # Clean shutdown of existing app
        if self.app:
            try:
                await self.app.shutdown()
                await self.app.stop()
            except:
                pass
        
        # Create new application
        self.app = Application.builder().token(config.BOT_TOKEN).build()
        
        # Setup handlers
        await self._setup_handlers()
    
    async def _clear_updates(self):
        """Clear webhook and pending updates"""
        try:
            await self.app.bot.delete_webhook(drop_pending_updates=True)
            await self.app.bot.get_me()  # Test connection
            logger.info("🧹 Cleared webhook and pending updates")
        except Exception as e:
            logger.warning(f"⚠️ Could not clear updates: {e}")
    
    async def _handle_conflict(self, attempt):
        """Handle conflict with intelligent waiting"""
        logger.info(f"🔧 Handling conflict (attempt {attempt})...")
        
        # Progressive wait times: 5s, 15s, 30s, 60s, 120s...
        wait_times = [5, 15, 30, 60, 120, 240, 480]
        wait_time = wait_times[min(attempt - 1, len(wait_times) - 1)]
        
        logger.info(f"⏳ Waiting {wait_time} seconds for other instances to timeout...")
        await asyncio.sleep(wait_time)
        
        # Try to force clear webhook
        try:
            from telegram import Bot
            temp_bot = Bot(config.BOT_TOKEN)
            await temp_bot.delete_webhook(drop_pending_updates=True)
            logger.info("🧹 Force cleared webhook")
        except Exception as e:
            logger.warning(f"⚠️ Force clear failed: {e}")

# Main execution
async def main():
    """Main bot execution with conflict protection"""
    bot = TeraboxBot()
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())
        
