"""
Bot handlers - Clean and organized
"""
import asyncio
from loguru import logger
from telegram import Update
from telegram.ext import ContextTypes

from .download import TeraboxDownloader
from .upload import TelegramUploader

class BotHandlers:
    def __init__(self):
        self.downloader = TeraboxDownloader()
        self.uploader = TelegramUploader()
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start"""
        user = update.effective_user
        await update.message.reply_text(
            f"🎉 Welcome {user.first_name}!\n\n"
            f"I'm your Terabox Leech Bot! 🚀\n\n"
            f"📥 Send me any Terabox link to download:\n"
            f"• terabox.com\n"
            f"• 1024terabox.com\n"
            f"• teraboxurl.com\n"
            f"• mirrobox.com\n\n"
            f"Just paste the link and I'll download it for you! ✨"
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help"""
        await update.message.reply_text(
            "📋 How to use:\n\n"
            "1. Copy any Terabox share link\n"
            "2. Send it to me\n"
            "3. Wait for download to complete\n"
            "4. Get your file!\n\n"
            "🔗 Supported domains:\n"
            "• terabox.com\n"
            "• 1024terabox.com\n"
            "• teraboxurl.com\n"
            "• mirrobox.com\n\n"
            "That's it! Simple and fast! ⚡"
        )
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats"""
        await update.message.reply_text("📊 Bot is running perfectly! ✅")
    
    async def verify_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /verify"""
        await update.message.reply_text("🔐 Verification system ready!")
    
    async def handle_terabox_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle Terabox links with organized download and upload"""
        user_id = update.effective_user.id
        text = update.message.text
        
        logger.info(f"📥 Download request from {user_id}: {text}")
        
        # Validate link
        text_lower = text.lower()
        is_valid = any(domain in text_lower for domain in [
            'terabox.com', '1024terabox.com', 'teraboxurl.com', 
            '4funbox.com', 'mirrobox.com', 'nephobox.com'
        ])
        
        if not is_valid:
            await update.message.reply_text(
                "❌ Invalid Terabox link!\n\n"
                "Please send a valid link like:\n"
                "https://terabox.com/s/xxxxx"
            )
            return
        
        # Start download process
        status_msg = await update.message.reply_text(
            f"📥 Processing Terabox Link...\n\n"
            f"🔗 {text[:60]}...\n"
            "⏳ Connecting to download servers..."
        )
        
        try:
            # Step 1: Get download info from API
            download_info = await self.downloader.get_download_info(text, status_msg)
            
            if not download_info['success']:
                await status_msg.edit_text(
                    f"❌ Failed to get download info\n\n"
                    f"Reason: {download_info['error']}"
                )
                return
            
            # Step 2: Download the actual file
            file_path = await self.downloader.download_file(
                download_info['download_url'],
                download_info['filename'],
                status_msg
            )
            
            if not file_path:
                await status_msg.edit_text("❌ File download failed")
                return
            
            # Step 3: Upload to Telegram
            upload_success = await self.uploader.upload_with_progress(
                update, file_path, download_info['filename'], status_msg
            )
            
            if upload_success:
                await status_msg.edit_text(
                    f"🎉 SUCCESS!\n\n"
                    f"📁 File: {download_info['filename']}\n"
                    f"💾 Size: {download_info['size']}\n"
                    f"⚡ Status: Uploaded to Telegram\n\n"
                    f"✨ Download complete!"
                )
            else:
                await status_msg.edit_text("❌ Upload to Telegram failed")
            
            # Step 4: Clean up downloaded file
            await self.downloader.cleanup_file(file_path)
                
        except Exception as e:
            logger.error(f"Download process error: {e}")
            await status_msg.edit_text(
                "❌ System Error\n\n"
                "Something went wrong. Please try again!"
            )
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular text"""
        await update.message.reply_text(
            "ℹ️ Send me a Terabox link!\n\n"
            "Examples:\n"
            "• https://terabox.com/s/xxxxx\n"
            "• https://1024terabox.com/s/xxxxx\n\n"
            "I'll download it for you! 🚀"
        )
