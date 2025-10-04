"""
Bot handlers - With debugging
"""
from loguru import logger
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from utils.helpers import is_owner, is_authorized, extract_terabox_url
import config

class BotHandlers:
    def __init__(self):
        self.active_downloads = {}
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start"""
        user = update.effective_user
        await update.message.reply_text(
            f"🎉 Welcome {user.first_name}!\n\n"
            f"I'm {config.BOT_NAME}\n\n"
            f"📥 Send me a Terabox link to download!\n\n"
            f"✅ Supported:\n"
            f"• terabox.com/s/xxx\n"
            f"• 1024terabox.com/s/xxx\n" 
            f"• teraboxurl.com/s/xxx",
            parse_mode=ParseMode.HTML
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help"""
        await update.message.reply_text(
            "📋 Commands:\n"
            "/start - Start bot\n"
            "/help - This message\n\n"
            "🔗 Just send any Terabox link!"
        )
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats"""
        if not is_owner(update.effective_user.id):
            await update.message.reply_text("❌ Owner only")
            return
        
        await update.message.reply_text(f"📊 {config.BOT_NAME} is running!")
    
    async def verify_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /verify"""
        await update.message.reply_text("🔐 Verification system ready!")
    
    async def handle_terabox_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle Terabox links - WITH DEBUGGING"""
        user_id = update.effective_user.id
        message_text = update.message.text
        
        logger.info(f"🔍 TERABOX HANDLER CALLED!")
        logger.info(f"📝 Message: {message_text}")
        logger.info(f"👤 User: {user_id}")
        
        # Extract URL
        terabox_url = extract_terabox_url(message_text)
        logger.info(f"🔗 Extracted URL: {terabox_url}")
        
        if not terabox_url:
            await update.message.reply_text(
                f"❌ Could not extract URL\n"
                f"📝 Your message: {message_text}"
            )
            return
        
        # Success - show we detected it
        await update.message.reply_text(
            f"🎉 LINK DETECTED!\n\n"
            f"🔗 URL: {terabox_url}\n"
            f"📝 Original: {message_text}\n\n"
            f"✅ Bot is working correctly!\n"
            f"⏳ Download function will be added next."
        )
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular text"""
        message_text = update.message.text
        logger.info(f"📝 Regular text received: {message_text}")
        
        await update.message.reply_text(
            f"ℹ️ This was not detected as Terabox link\n\n"
            f"📝 Your message: {message_text}\n\n"
            f"✅ Send: terabox.com/s/xxx or similar"
                                 )
        
