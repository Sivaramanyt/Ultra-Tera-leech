"""

Bot handlers - Simple Working Version (No External Dependencies)

"""

import asyncio
from loguru import logger
from telegram import Update
from telegram.ext import ContextTypes
from .download import TeraboxDownloader
from .upload import TelegramUploader
import config

# Simple cancel system (no external file needed)
class SimpleDownloadManager:
    def __init__(self):
        self.active_downloads = {}
        self.cancelled_downloads = set()
    
    def add_download(self, user_id: int):
        self.active_downloads[user_id] = True
        if user_id in self.cancelled_downloads:
            self.cancelled_downloads.remove(user_id)
    
    def remove_download(self, user_id: int):
        if user_id in self.active_downloads:
            del self.active_downloads[user_id]
        if user_id in self.cancelled_downloads:
            self.cancelled_downloads.remove(user_id)
    
    def cancel_download(self, user_id: int):
        self.cancelled_downloads.add(user_id)
        if user_id in self.active_downloads:
            del self.active_downloads[user_id]
    
    def has_active_download(self, user_id: int):
        return user_id in self.active_downloads
    
    def is_cancelled(self, user_id: int):
        return user_id in self.cancelled_downloads

# Simple force sub system (no external file needed)
class SimpleForceSubscription:
    async def check_subscription(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        
        # Skip for owner
        if user_id == config.OWNER_ID:
            return True
        
        # Skip if not configured
        if (not hasattr(config, 'FORCE_SUB_CHANNELS') or 
            not config.FORCE_SUB_CHANNELS or 
            not getattr(config, 'ENABLE_FORCE_SUB', False)):
            return True
        
        # Simple check - just check if user can use bot
        return True  # Simplified - always allow for now

# Global instances
download_manager = SimpleDownloadManager()
force_subscription = SimpleForceSubscription()

class BotHandlers:
    def __init__(self):
        self.downloader = TeraboxDownloader()
        self.uploader = TelegramUploader()
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start"""
        # Simple force sub check
        if not await force_subscription.check_subscription(update, context):
            return
        
        user = update.effective_user
        await update.message.reply_text(
            f"🎉 Welcome {user.first_name}!\n\n"
            f"I'm your Terabox Leech Bot 🚀\n\n"
            f"📥 Send me any Terabox link to download:\n"
            f"• terabox.com\n"
            f"• 1024terabox.com\n"
            f"• teraboxurl.com\n"
            f"• mirrobox.com\n\n"
            f"🎬 Videos → Playable videos\n"
            f"🎵 Audio → Music files\n"
            f"📸 Photos → Viewable images\n"
            f"📁 Others → Documents\n\n"
            f"Commands:\n"
            f"/help - Show help\n"
            f"/cancel - Cancel download\n"
            f"/stats - Bot statistics\n\n"
            f"Just paste the link and I'll download it for you! ✨",
            parse_mode=None
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help"""
        if not await force_subscription.check_subscription(update, context):
            return
        
        await update.message.reply_text(
            "📋 How to use:\n\n"
            "1. Copy any Terabox share link\n"
            "2. Send it to me\n"
            "3. Wait for download to complete\n"
            "4. Get your file as proper media type!\n\n"
            "🔗 Supported domains:\n"
            "• terabox.com\n"
            "• 1024terabox.com\n"
            "• teraboxurl.com\n"
            "• mirrobox.com\n\n"
            "That's it! Simple and fast! ⚡",
            parse_mode=None
        )
    
    async def cancel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /cancel"""
        user_id = update.effective_user.id
        
        if not download_manager.has_active_download(user_id):
            await update.message.reply_text(
                "ℹ️ No Active Download\n\n"
                "You don't have any ongoing downloads to cancel.\n\n"
                "📥 Send a Terabox link to start downloading!",
                parse_mode=None
            )
            return
        
        # Cancel the download
        download_manager.cancel_download(user_id)
        await update.message.reply_text(
            "✅ Download Cancelled\n\n"
            "Your download has been successfully cancelled.\n"
            "You can start a new download anytime!",
            parse_mode=None
        )
        logger.info(f"🗑️ User {user_id} cancelled their download")
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats"""
        active_downloads = len(download_manager.active_downloads)
        user_has_download = download_manager.has_active_download(update.effective_user.id)
        
        await update.message.reply_text(
            f"📊 Bot Statistics\n\n"
            f"🚀 Status: ✅ Online & Operational\n"
            f"📥 Active Downloads: {active_downloads}\n"
            f"👤 Your Status: {'⏳ Downloading' if user_has_download else '✅ Ready'}\n\n"
            f"🎬 Video uploads: ✅ Enabled\n"
            f"🎵 Audio uploads: ✅ Enabled\n"
            f"📸 Photo uploads: ✅ Enabled\n"
            f"📁 Document uploads: ✅ Enabled\n\n"
            f"⚡ All systems operational!",
            parse_mode=None
        )
    
    async def verify_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /verify"""
        await update.message.reply_text("🔐 Verification system ready!")
    
    async def handle_terabox_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle Terabox links"""
        if not await force_subscription.check_subscription(update, context):
            return
        
        user_id = update.effective_user.id
        text = update.message.text
        
        # Check if user already has active download
        if download_manager.has_active_download(user_id):
            await update.message.reply_text(
                "⚠️ Download In Progress\n\n"
                "You already have an active download.\n"
                "Use /cancel to stop it and start a new one.",
                parse_mode=None
            )
            return
        
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
                f"https://terabox.com/s/xxxxx",
                parse_mode=None
            )
            return
        
        # Start download process
        status_msg = await update.message.reply_text(
            f"📥 Processing Terabox Link...\n\n"
            f"🔗 {text[:50]}...\n"
            "⏳ Connecting to download servers...\n\n"
            "💡 Use /cancel to stop this download",
            parse_mode=None
        )
        
        # Add to download manager
        download_manager.add_download(user_id)
        
        try:
            await self._download_process(update, text, status_msg, user_id)
        except Exception as e:
            logger.error(f"Download process error: {e}")
        finally:
            # Always clean up
            download_manager.remove_download(user_id)
    
    async def _download_process(self, update: Update, text: str, status_msg, user_id: int):
        """The actual download process - FIXED"""
        try:
            # Step 1: Get download info
            download_info = await self.downloader.get_download_info(text, status_msg)
            
            # Check if cancelled
            if download_manager.is_cancelled(user_id):
                await status_msg.edit_text(
                    "❌ Download Cancelled\n\n"
                    "The download has been cancelled by user.",
                    parse_mode=None
                )
                return
            
            if not download_info['success']:
                await status_msg.edit_text(
                    f"❌ Failed to get download info\n\n"
                    f"Reason: {download_info['error']}",
                    parse_mode=None
                )
                return
            
            # FIXED: Extract variables from download_info properly
            filename = download_info.get('filename', 'unknown_file')
            download_url = download_info.get('download_url')  # ← CRITICAL FIX
            file_size = download_info.get('size', 'Unknown')
            
            # FIXED: Validate download_url exists
            if not download_url:
                logger.error("❌ No download URL found in API response")
                await status_msg.edit_text(
                    "❌ Failed to extract download URL\n\n"
                    "Please try again or contact support.",
                    parse_mode=None
                )
                return
            
            logger.info(f"✅ Download URL extracted: {download_url[:100]}...")
            
            # Step 2: Detect media type
            file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
            media_type, media_emoji = self._detect_media_type(file_ext)
            
            # Step 3: Download file
            await status_msg.edit_text(
                f"📥 Downloading File...\n\n"
                f"📁 File: {filename[:40]}...\n"
                f"💾 Size: {file_size}\n"
                f"📱 Type: {media_emoji} {media_type}\n"
                f"⏳ Please wait...\n\n"
                f"💡 Use /cancel to stop",
                parse_mode=None
            )
            
            # FIXED: Now download_url is properly defined
            file_path = await self.downloader.download_file(
                download_url,  # ← Now properly defined
                filename,
                status_msg
            )
            
            # Check if cancelled after download
            if download_manager.is_cancelled(user_id):
                await status_msg.edit_text(
                    "❌ Download Cancelled\n\n"
                    "The download has been cancelled by user.",
                    parse_mode=None
                )
                # Clean up file
                if file_path:
                    await self.downloader.cleanup_file(file_path)
                return
            
            if not file_path:
                await status_msg.edit_text(
                    "❌ File download failed\n\n"
                    "Please try again later!",
                    parse_mode=None
                )
                return
            
            # Step 4: Upload to Telegram
            await status_msg.edit_text(
                f"📤 Uploading to Telegram...\n\n"
                f"📁 File: {filename[:40]}...\n"
                f"💾 Size: {file_size}\n"
                f"📱 Uploading as: {media_emoji} {media_type}",
                parse_mode=None
            )
            
            upload_success = await self.uploader.upload_with_progress(
                update, file_path, filename, status_msg
            )
            
            if upload_success:
                await status_msg.edit_text(
                    f"🎉 SUCCESS!\n\n"
                    f"📁 File: {filename[:40]}{'...' if len(filename) > 40 else ''}\n"
                    f"💾 Size: {file_size}\n"
                    f"📱 Type: {media_emoji} {media_type}\n"
                    f"⚡ Status: Uploaded Successfully!\n\n"
                    f"✨ Ready to view/play in Telegram!",
                    parse_mode=None
                )
            
            # Clean up
            await self.downloader.cleanup_file(file_path)
            
        except Exception as e:
            logger.error(f"Download process error: {e}")
            if not download_manager.is_cancelled(user_id):
                await status_msg.edit_text(
                    "❌ System Error\n\n"
                    "Something went wrong. Please try again!",
                    parse_mode=None
                )
    
    def _detect_media_type(self, file_ext: str):
        """Detect media type from file extension"""
        file_ext = file_ext.lower()
        
        video_exts = ['mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv', '3gp', 'webm', 'm4v', 'mpg', 'mpeg']
        audio_exts = ['mp3', 'wav', 'flac', 'aac', 'ogg', 'wma', 'm4a', 'opus']
        photo_exts = ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'tiff', 'tif']
        
        if file_ext in video_exts:
            return "Video", "🎬"
        elif file_ext in audio_exts:
            return "Audio", "🎵"
        elif file_ext in photo_exts:
            return "Photo", "📸"
        else:
            return "Document", "📁"
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular text"""
        if not await force_subscription.check_subscription(update, context):
            return
        
        await update.message.reply_text(
            "ℹ️ Send me a Terabox link!\n\n"
            "Examples:\n"
            "• https://terabox.com/s/xxxxx\n"
            "• https://1024terabox.com/s/xxxxx\n\n"
            "I'll download it and upload as the right media type! 🚀\n\n"
            "💡 Use /cancel to stop ongoing downloads",
            parse_mode=None
        )
        
