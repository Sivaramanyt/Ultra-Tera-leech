"""
Simple Working Bot Core - Back to Basics
"""
import asyncio
from telegram.ext import Application, CommandHandler, MessageHandler, filters
from loguru import logger
import config

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

async def main():
    """Main bot function - Simple and Working"""
    try:
        logger.info(f"🤖 Starting terabox_bot...")
        
        # Create application
        app = Application.builder().token(config.BOT_TOKEN).build()
        
        # Setup handlers
        await _setup_handlers(app)
        
        # Clear updates
        await _clear_updates(app)
        
        # Start bot
        logger.info("🚀 Starting Terabox Leech Bot...")
        await app.run_polling(
            drop_pending_updates=True,
            allowed_updates=['message', 'callback_query']
        )
        
    except Exception as e:
        logger.error(f"Bot startup failed: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(main())
    
