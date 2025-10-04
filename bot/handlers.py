"""
Bot handlers - Complete Version with Media Type Upload
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
            f"I'm your **Terabox Leech Bot** 🚀\n\n"
            f"📥 **Send me any Terabox link to download:**\n"
            f"• terabox.com\n"
            f"• 1024terabox.com\n"
            f"• teraboxurl.com\n"
            f"• mirrobox.com\n\n"
            f"🎬 **Videos** → Uploaded as playable videos\n"
            f"🎵 **Audio** → Uploaded as music files\n"
            f"📸 **Photos** → Uploaded as viewable images\n"
            f"📁 **Others** → Uploaded as documents\n\n"
            f"Just paste the link and I'll download it for you! ✨",
            parse_mode='Markdown'
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help"""
        await update.message.reply_text(
            "📋 **How to use:**\n\n"
            "1. Copy any Terabox share link\n"
            "2. Send it to me\n"
            "3. Wait for download to complete\n"
            "4. Get your file as proper media type!\n\n"
            "🔗 **Supported domains:**\n"
            "• terabox.com\n"
            "• 1024terabox.com\n"
            "• teraboxurl.com\n"
            "• mirrobox.com\n\n"
            "📱 **Media Types:**\n"
            "🎬 Videos (mp4, avi, mkv, mov, etc.)\n"
            "🎵 Audio (mp3, wav, flac, aac, etc.)\n"
            "📸 Photos (jpg, png, gif, etc.)\n"
            "📁 Documents (pdf, zip, etc.)\n\n"
            "That's it! Simple and fast! ⚡",
            parse_mode='Markdown'
        )
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats"""
        await update.message.reply_text(
            "📊 **Bot Status:** ✅ Online\n\n"
            "🎬 Video uploads: Enabled\n"
            "🎵 Audio uploads: Enabled\n"
            "📸 Photo uploads: Enabled\n"
            "📁 Document uploads: Enabled\n\n"
            "🚀 All systems operational!",
            parse_mode='Markdown'
        )
    
    async def verify_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /verify"""
        await update.message.reply_text("🔐 Verification system ready!")
    
    async def handle_terabox_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle Terabox links with media type detection and upload"""
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
                "❌ **Invalid Terabox link!**\n\n"
                "Please send a valid link like:\n"
                "`https://terabox.com/s/xxxxx`\n\n"
                "Supported domains:\n"
                "• terabox.com\n"
                "• 1024terabox.com\n"
                "• teraboxurl.com\n"
                "• mirrobox.com",
                parse_mode='Markdown'
            )
            return
        
        # Start download process
        status_msg = await update.message.reply_text(
            f"📥 **Processing Terabox Link...**\n\n"
            f"🔗 `{text[:50]}...`\n"
            "⏳ Connecting to download servers...",
            parse_mode='Markdown'
        )
        
        try:
            # Step 1: Get download info from API
            logger.info("🔍 Getting download info from APIs...")
            download_info = await self.downloader.get_download_info(text, status_msg)
            
            if not download_info['success']:
                await status_msg.edit_text(
                    f"❌ **Failed to get download info**\n\n"
                    f"**Reason:** {download_info['error']}\n\n"
                    f"💡 **Try:**\n"
                    f"• Check if the link is valid\n"
                    f"• Try again in a few minutes\n"
                    f"• Use a different Terabox link",
                    parse_mode='Markdown'
                )
                return
            
            logger.info(f"✅ Got download info: {download_info['filename']}")
            
            # Step 2: Detect media type before download
            file_ext = download_info['filename'].lower().split('.')[-1] if '.' in download_info['filename'] else ''
            media_type, media_emoji = self._detect_media_type(file_ext)
            
            logger.info(f"📱 Detected media type: {media_type} ({file_ext})")
            
            # Step 3: Download the actual file
            await status_msg.edit_text(
                f"📥 **Downloading File...**\n\n"
                f"📁 **File:** {download_info['filename'][:40]}...\n"
                f"💾 **Size:** {download_info['size']}\n"
                f"📱 **Type:** {media_emoji} {media_type}\n"
                f"⏳ Please wait...",
                parse_mode='Markdown'
            )
            
            file_path = await self.downloader.download_file(
                download_info['download_url'],
                download_info['filename'],
                status_msg
            )
            
            if not file_path:
                await status_msg.edit_text(
                    "❌ **File download failed**\n\n"
                    "The file could not be downloaded.\n"
                    "This might be due to:\n"
                    "• Server timeout\n"
                    "• Invalid download link\n"
                    "• Network issues\n\n"
                    "Please try again later!",
                    parse_mode='Markdown'
                )
                return
            
            logger.info(f"✅ File downloaded: {file_path}")
            
            # Step 4: Upload to Telegram as appropriate media type
            await status_msg.edit_text(
                f"📤 **Uploading to Telegram...**\n\n"
                f"📁 **File:** {download_info['filename'][:40]}...\n"
                f"💾 **Size:** {download_info['size']}\n"
                f"📱 **Uploading as:** {media_emoji} {media_type}\n"
                f"⏳ Please wait...",
                parse_mode='Markdown'
            )
            
            upload_success = await self.uploader.upload_with_progress(
                update, file_path, download_info['filename'], status_msg
            )
            
            if upload_success:
                await status_msg.edit_text(
                    f"🎉 **SUCCESS!**\n\n"
                    f"📁 **File:** {download_info['filename'][:40]}{'...' if len(download_info['filename']) > 40 else ''}\n"
                    f"💾 **Size:** {download_info['size']}\n"
                    f"📱 **Type:** {media_emoji} {media_type}\n"
                    f"⚡ **Status:** Uploaded Successfully!\n\n"
                    f"✨ Ready to view/play in Telegram!",
                    parse_mode='Markdown'
                )
                logger.info(f"✅ Upload successful: {media_type}")
            else:
                await status_msg.edit_text(
                    "❌ **Upload to Telegram failed**\n\n"
                    "The file was downloaded but couldn't be uploaded.\n"
                    "This might be due to:\n"
                    "• File too large (>50MB)\n"
                    "• Invalid file format\n"
                    "• Telegram server issues\n\n"
                    "Please try with a smaller file!",
                    parse_mode='Markdown'
                )
                logger.error("❌ Upload failed")
            
            # Step 5: Clean up downloaded file
            await self.downloader.cleanup_file(file_path)
            logger.info("🧹 Cleanup completed")
                
        except Exception as e:
            logger.error(f"Download process error: {e}")
            await status_msg.edit_text(
                "❌ **System Error**\n\n"
                "Something went wrong during processing.\n"
                "Please try again in a moment!\n\n"
                "If the problem persists, the file might be:\n"
                "• Too large\n"
                "• Corrupted\n"
                "• Protected",
                parse_mode='Markdown'
            )
    
    def _detect_media_type(self, file_ext: str):
        """Detect media type from file extension"""
        file_ext = file_ext.lower()
        
        # Video extensions
        video_exts = [
            'mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv', '3gp', 'webm', 
            'm4v', 'mpg', 'mpeg', 'ogv', 'ts', 'vob', 'asf', 'rm', 'rmvb'
        ]
        
        # Audio extensions  
        audio_exts = [
            'mp3', 'wav', 'flac', 'aac', 'ogg', 'wma', 'm4a', 'opus', 
            'aiff', 'au', 'ra', 'amr', '3ga', 'ac3', 'dts'
        ]
        
        # Photo extensions
        photo_exts = [
            'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'tiff', 'tif', 
            'svg', 'ico', 'heic', 'heif'
        ]
        
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
        await update.message.reply_text(
            "ℹ️ **Send me a Terabox link!**\n\n"
            "**Examples:**\n"
            "• `https://terabox.com/s/xxxxx`\n"
            "• `https://1024terabox.com/s/xxxxx`\n"
            "• `https://teraboxurl.com/s/xxxxx`\n\n"
            "I'll download it and upload as the right media type! 🚀\n\n"
            "🎬 Videos → Playable videos\n"
            "🎵 Audio → Music files\n"
            "📸 Photos → Viewable images\n"
            "📁 Others → Documents",
            parse_mode='Markdown'
    )
        
