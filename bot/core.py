"""
Core bot functionality and initialization
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
        """Setup all handlers"""
        # Commands
        self.application.add_handler(CommandHandler("start", self.handlers.start_command))
        self.application.add_handler(CommandHandler("help", self.handlers.help_command))
        self.application.add_handler(CommandHandler("stats", self.handlers.stats_command))
        self.application.add_handler(CommandHandler("verify", self.handlers.verify_command))
        
        # Messages
        self.application.add_handler(MessageHandler(TeraboxFilter(), self.handlers.handle_terabox_link))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handlers.handle_text))
        
        # Callbacks
        self.application.add_handler(CallbackQueryHandler(self.callbacks.handle_callback))
        
        logger.info("✅ Handlers setup complete")
    
    def run(self):
        """Run bot (synchronous method for Docker)"""
        logger.info("🤖 Bot starting...")
        try:
            # Use run_polling without await - it handles the event loop internally
            self.application.run_polling(
                drop_pending_updates=True,
                allowed_updates=['message', 'callback_query']
            )
        except Exception as e:
            logger.error(f"Bot run error: {e}")
            raise
            
