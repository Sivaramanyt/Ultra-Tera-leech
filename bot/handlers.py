"""
Bot handlers - Simplified for testing
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
            f"I'm {config.BOT_NAME} - Send me a Terabox link to download!",
            parse_mode=ParseMode.HTML
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help"""
        await update.message.reply_text(
            "📋 Commands:\n"
            "/start - Start bot\n"
            "/help - This message\n\n"
            "🔗 Just send any Terabox link to download!"
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
        """Handle Terabox links - FIXED"""
        user_id = update.effective_user.id
        
        logger.info(f"📥 Terabox link from user {user_id}")
        
        # Extract URL
        terabox_url = extract_terabox_url(update.message.text)
        if not terabox_url:
            await update.message.reply_text("❌ Invalid Terabox link")
            return
        
        logger.info(f"🔗 Processing URL: {terabox_url}")
        
        # Send processing message
        status_msg = await update.message.reply_text(
            f"📥 Processing Terabox link...\n🔗 {terabox_url[:50]}..."
        )
        
        # Simulate download (replace this with actual download later)
        await status_msg.edit_text(
            f"📥 Downloading from Terabox...\n"
            f"📊 Progress: 50%\n"
            f"[█████░░░░░]\n"
            f"⚡ Speed: 2.5 MB/s"
        )
        
        # For now, send a test response
        await status_msg.edit_text(
            f"✅ Download would start here!\n"
            f"🔗 URL: {terabox_url}\n"
            f"📝 Status: Link detected successfully!\n\n"
            f"⚠️ Download function needs to be connected."
        )
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages"""
        await update.message.reply_text(
            "ℹ️ Send me a Terabox link to download!\n\n"
            "Supported: terabox.com, 1024terabox.com, teraboxurl.com"
        )
        
