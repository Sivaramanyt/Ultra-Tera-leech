"""
Core bot functionality - Complete with all handlers
"""
from loguru import logger
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler

from .handlers import BotHandlers
from .callbacks import CallbackHandlers
from .filters import TeraboxFilter
import config

class TeraboxBot:
    def __init__(self):
        # Add unique ID to prevent conflicts
        self.app_id = f"terabox_bot_{hash(config.BOT_TOKEN) % 10000}"
        
        self.application = Application.builder().token(config.BOT_TOKEN).build()
        self.handlers = BotHandlers()
        self.callbacks = CallbackHandlers()
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup all handlers"""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.handlers.start_command))
        self.application.add_handler(CommandHandler("help", self.handlers.help_command))
        self.application.add_handler(CommandHandler("stats", self.handlers.stats_command))
        self.application.add_handler(CommandHandler("verify", self.handlers.verify_command))
        
        # Cancel command (if enabled)
        if config.ENABLE_CANCEL_COMMAND:
            self.application.add_handler(CommandHandler("cancel", self.handlers.cancel_command))
        
        # Message handlers
        terabox_filter = TeraboxFilter()
        self.application.add_handler(
            MessageHandler(terabox_filter, self.handlers.handle_terabox_link)
        )
        self.application.add_handler(
            MessageHandler(filters.TEXT & ~filters.COMMAND, self.handlers.handle_text)
        )
        
        # Callback query handler
        self.application.add_handler(CallbackQueryHandler(self.callbacks.handle_callback))
        
        # Error handler
        self.application.add_error_handler(self._error_handler)
        
        logger.info(f"✅ Handlers ready for {self.app_id}")
    
    async def _error_handler(self, update, context):
        """Handle bot errors"""
        logger.error(f"Bot error: {context.error}")
        
        # Handle specific error types
        if "Conflict" in str(context.error):
            logger.warning("Conflict detected - another bot instance may be running")
            return
        
        if update and update.effective_message:
            try:
                await update.effective_message.reply_text(
                    "❌ An error occurred. Please try again."
                )
            except:
                pass
    
    def run(self):
        """Run bot with advanced conflict handling"""
        logger.info(f"🤖 Starting {self.app_id}...")
        
        try:
            # Force clear any existing updates
            import asyncio
            asyncio.get_event_loop().run_until_complete(self._clear_updates())
            
            # Start polling
            self.application.run_polling(
                drop_pending_updates=True,
                close_loop=False,
                stop_signals=None,
                allowed_updates=['message', 'callback_query']
            )
            
        except Exception as e:
            logger.error(f"❌ Bot run error: {e}")
            raise
    
    async def _clear_updates(self):
        """Force clear any pending updates"""
        try:
            await self.application.bot.delete_webhook(drop_pending_updates=True)
            logger.info("🧹 Cleared webhook and pending updates")
        except Exception as e:
            logger.warning(f"Failed to clear updates: {e}")
        
