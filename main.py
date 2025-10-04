"""
Terabox Leech Bot - Main Entry Point
"""
import os
import sys
from loguru import logger

# Add to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bot.core import TeraboxBot
import config

# Setup logging
logger.add(
    "logs/bot.log",
    rotation="10 MB",
    retention="7 days",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
)

def main():
    """Start the bot"""
    try:
        logger.info(f"🚀 Starting {config.BOT_NAME}...")
        
        # Create directories
        os.makedirs(config.DOWNLOAD_DIR, exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        
        # Start bot (synchronous)
        bot = TeraboxBot()
        bot.run()
        
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"❌ Bot failed: {e}")
        raise

if __name__ == "__main__":
    main()
    
