"""
Core bot functionality - Simple Fixed Version
"""
from loguru import logger
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackQueryHandler

from .handlers import BotHandlers
from .callbacks import CallbackHandlers
from .filters import TeraboxFilter
import config

class TeraboxBot:
    def __init__(self):
        self.application = Application.builder().token(config.BOT_TOKEN).build()
        self.handlers = BotHandlers()
        self.callbacks = CallbackHandlers()
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup handlers"""
        self.application.add_handler(CommandHandler("start", self.handlers.start_command))
        self.application.add_handler(CommandHandler("help", self.handlers.help_command))
        self.application.add_handler(CommandHandler("stats", self.handlers.stats_command))
        self.application.add_handler(CommandHandler("verify", self.handlers.verify_command))
        
        terabox_filter = TeraboxFilter()
        self.application.add_handler(MessageHandler(terabox_filter, self.handlers.handle_terabox_link))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handlers.handle_text))
        self.application.add_handler(CallbackQueryHandler(self.callbacks.handle_callback))
        
        logger.info("✅ Handlers ready")
    
    def run(self):
        """Run bot"""
        logger.info("🤖 Starting bot...")
        try:
            # Clear any existing updates and start fresh
            self.application.run_polling(drop_pending_updates=True)
        except Exception as e:
            logger.error(f"Error: {e}")
            if "Conflict" in str(e):
                logger.info("Multiple instances detected. Stopping other instances...")
                import time
                time.sleep(15)  # Wait for other instances to stop
                self.run()  # Retry
            else:
                raise
                
