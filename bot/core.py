"""
Simple Working Bot Core with Conflict Resolution
"""
import asyncio
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from telegram.error import Conflict, TimedOut, NetworkError
from telegram import Update
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
    
    # Add error handler for conflicts
    app.add_error_handler(_error_handler)
    
    logger.info(f"✅ Handlers ready for terabox_bot")

async def _error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle bot errors including conflicts"""
    error = context.error
    
    if isinstance(error, Conflict):
        logger.error(f"Bot error: {error}")
        logger.warning("Conflict detected - another bot instance may be running")
        # The conflict will be handled by the retry mechanism in main()
        return
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

async def _handle_conflict(attempt):
    """Handle conflict with progressive backoff"""
    logger.info(f"🔧 Handling conflict (attempt {attempt})...")
    
    # Progressive wait times: 5s, 15s, 30s, 60s, 120s...
    wait_times = [5, 15, 30, 60, 120, 240]
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

async def main():
    """Main bot function with conflict handling"""
    max_retries = 8
    base_delay = 3
    
    for attempt in range(max_retries):
        try:
            logger.info(f"🤖 Starting terabox_bot (attempt {attempt + 1}/{max_retries})...")
            
            # Create application
            app = Application.builder().token(config.BOT_TOKEN).build()
            
            # Setup handlers
            await _setup_handlers(app)
            
            # Clear updates
            await _clear_updates(app)
            
            # Start bot with conflict-resistant settings
            logger.info("🚀 Starting Terabox Leech Bot...")
            await app.run_polling(
                drop_pending_updates=True,
                allowed_updates=['message', 'callback_query'],
                poll_interval=2.0,        # 2 second polling interval
                timeout=20,               # 20 second timeout
                bootstrap_retries=5,      # More bootstrap retries
                read_timeout=15,          # Longer read timeout
                write_timeout=15,         # Longer write timeout
                connect_timeout=15,       # Longer connect timeout
                pool_timeout=15           # Longer pool timeout
            )
            
            # If we reach here, bot started successfully
            return
            
        except Conflict as e:
            logger.warning(f"🔄 Conflict on attempt {attempt + 1}: {e}")
            
            if attempt < max_retries - 1:
                await _handle_conflict(attempt + 1)
            else:
                logger.error("❌ Max conflict retries reached")
                # Try one last time with longer wait
                logger.info("🔄 Final attempt with extended wait...")
                await asyncio.sleep(300)  # 5 minutes
                # Don't break here, let it try one more time
                
        except Exception as e:
            logger.error(f"❌ Error on attempt {attempt + 1}: {e}")
            
            if attempt < max_retries - 1:
                wait_time = base_delay * (2 ** attempt)  # Exponential backoff
                logger.info(f"⏳ Retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
            else:
                logger.error("❌ Max retries reached")
                raise

if __name__ == "__main__":
    asyncio.run(main())
    
