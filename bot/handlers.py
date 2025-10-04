"""
Bot handlers - Final Complete Version with All Features
"""
import asyncio
from loguru import logger
from telegram import Update
from telegram.ext import ContextTypes

from .download import TeraboxDownloader
from .upload import TelegramUploader
from .cancel import download_canceler
from .force_sub import force_subscription
import config

class BotHandlers:
    def __init__(self):
        self.downloader = TeraboxDownloader()
        self.uploader = TelegramUploader()
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        # Check force subscription first
        if config.ENABLE_FORCE_SUB and not await force_subscription.check_subscription(update, context):
            return
        
        user = update.effective_user
        
        # Get user stats
        active_downloads = len(download_canceler.active_downloads)
        user_has_download = download_canceler.has_active_download(user.id)
        
        await update.message.reply_text(
            f"🎉 **Welcome {user.first_name}!**\n\n"
            f"I'm your **{config.BOT_NAME}** 🚀\n\n"
            f"📥 **Send me any Terabox link to download:**\n"
            f"• terabox.com\n"
            f"• 1024terabox.com\n"
            f"• teraboxurl.com\n"
            f"• mirrobox.com\n\n"
            f"📱 **Auto Media Type Detection:**\n"
            f"🎬 **Videos** → Playable videos\n"
            f"🎵 **Audio** → Music files\n"
            f"📸 **Photos** → Viewable images\n"
            f"📁 **Others** → Documents\n\n"
            f"⚙️ **Available Commands:**\n"
            f"/help - Show detailed help\n"
            f"/cancel - Cancel ongoing download\n"
            f"/stats - Bot statistics\n\n"
            f"📊 **Current Status:**\n"
            f"🔥 Active Downloads: {active_downloads}\n"
            f"📥 Your Download: {'⏳ In Progress' if user_has_download else '✅ Ready'}\n\n"
            f"Just paste any Terabox link and I'll handle the rest! ✨",
            parse_mode='Markdown'
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        # Check force subscription first
        if config.ENABLE_FORCE_SUB and not await force_subscription.check_subscription(update, context):
            return
        
        await update.message.reply_text(
            f"📋 **{config.BOT_NAME} - Complete Guide**\n\n"
            f"**🚀 How to use:**\n"
            f"1. Copy any Terabox share link\n"
            f"2. Send it to me\n"
            f"3. Wait for download to complete\n"
            f"4. Get your file as proper media type!\n\n"
            f"**⚙️ Commands:**\n"
            f"• `/start` - Start the bot\n"
            f"• `/help` - Show this help\n"
            f"• `/cancel` - Cancel ongoing download\n"
            f"• `/stats` - Bot statistics\n\n"
            f"**🔗 Supported domains:**\n"
            f"• terabox.com\n"
            f"• 1024terabox.com\n"
            f"• teraboxurl.com\n"
            f"• mirrobox.com\n"
            f"• 4funbox.com\n"
            f"• nephobox.com\n\n"
            f"**📱 Media Type Auto-Detection:**\n"
            f"🎬 **Videos:** mp4, avi, mkv, mov, wmv, flv, 3gp, webm\n"
            f"🎵 **Audio:** mp3, wav, flac, aac, ogg, wma, m4a, opus\n"
            f"📸 **Photos:** jpg, jpeg, png, gif, bmp, webp, tiff\n"
            f"📁 **Documents:** pdf, zip, rar, doc, txt, etc.\n\n"
            f"**⚡ Features:**\n"
            f"• Real-time progress updates\n"
            f"• Automatic file type detection\n"
            f"• Cancellable downloads\n"
            f"• Multiple format support\n"
            f"• Fast and reliable\n\n"
            f"**📏 Limits:**\n"
            f"• Max file size: {config.MAX_FILE_SIZE // (1024*1024)}MB\n"
            f"• One download per user at a time\n\n"
            f"That's it! Simple and fast! 🎯",
            parse_mode='Markdown'
        )
    
    async def cancel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /cancel command"""
        # Check force subscription first
        if config.ENABLE_FORCE_SUB and not await force_subscription.check_subscription(update, context):
            return
        
        user_id = update.effective_user.id
        
        if not download_canceler.has_active_download(user_id):
            await update.message.reply_text(
                "ℹ️ **No Active Download**\n\n"
                "You don't have any ongoing downloads to cancel.\n\n"
                "📥 Send a Terabox link to start downloading!\n"
                "🔗 Supported: terabox.com, 1024terabox.com, etc.",
                parse_mode='Markdown'
            )
            return
        
        # Show cancellation confirmation
        await update.message.reply_text(
            "⏳ **Cancelling Download...**\n\n"
            "Please wait while I stop the download and clean up files.",
            parse_mode='Markdown'
        )
        
        # Cancel the download
        cancelled = await download_canceler.cancel_download(user_id)
        
        if cancelled:
            await update.message.reply_text(
                "✅ **Download Cancelled Successfully**\n\n"
                "Your download has been stopped and files cleaned up.\n\n"
                "📥 You can start a new download anytime!\n"
                "🚀 Just send another Terabox link.",
                parse_mode='Markdown'
            )
            logger.info(f"🗑️ User {user_id} cancelled their download successfully")
        else:
            await update.message.reply_text(
                "❌ **Cancellation Failed**\n\n"
                "Could not cancel the download.\n"
                "It might have already completed or failed.\n\n"
                "📊 Check /stats for current status.",
                parse_mode='Markdown'
            )
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats command"""
        # Check force subscription first
        if config.ENABLE_FORCE_SUB and not await force_subscription.check_subscription(update, context):
            return
        
        user_id = update.effective_user.id
        active_downloads = len(download_canceler.active_downloads)
        user_has_download = download_canceler.has_active_download(user_id)
        
        # Additional stats for owner
        if user_id == config.OWNER_ID:
            owner_stats = (
                f"\n**👑 Owner Statistics:**\n"
                f"📊 Total active downloads: {active_downloads}\n"
                f"👥 Users downloading: {len(download_canceler.active_downloads)}\n"
                f"⚙️ Force subscription: {'✅ Enabled' if config.ENABLE_FORCE_SUB else '❌ Disabled'}\n"
                f"🔧 Cancel command: {'✅ Enabled' if config.ENABLE_CANCEL_COMMAND else '❌ Disabled'}"
            )
        else:
            owner_stats = ""
        
        await update.message.reply_text(
            f"📊 **Bot Statistics**\n\n"
            f"🚀 **Status:** ✅ Online & Operational\n"
            f"📥 **Active Downloads:** {active_downloads}\n"
            f"👤 **Your Status:** {'⏳ Downloading' if user_has_download else '✅ Ready'}\n\n"
            f"🎬 **Supported Features:**\n"
            f"• Video uploads: ✅ Enabled\n"
            f"• Audio uploads: ✅ Enabled\n"
            f"• Photo uploads: ✅ Enabled\n"
            f"• Document uploads: ✅ Enabled\n"
            f"• Download cancellation: ✅ Enabled\n"
            f"• Progress tracking: ✅ Enabled\n\n"
            f"📏 **Limits:**\n"
            f"• Max file size: {config.MAX_FILE_SIZE // (1024*1024)}MB\n"
            f"• Concurrent downloads: 1 per user\n\n"
            f"⚡ **Server Status:** All systems operational!"
            f"{owner_stats}",
            parse_mode='Markdown'
        )
    
    async def verify_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /verify command (placeholder for future verification system)"""
        await update.message.reply_text(
            "🔐 **Verification System**\n\n"
            "✅ Your access is verified!\n"
            "🚀 You can use all bot features.\n\n"
            "📋 Current verification status: **Active**",
            parse_mode='Markdown'
        )
    
    async def handle_terabox_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle Terabox links with complete functionality"""
        # Check force subscription first
        if config.ENABLE_FORCE_SUB and not await force_subscription.check_subscription(update, context):
            return
        
        user_id = update.effective_user.id
        text = update.message.text
        
        # Check if user already has active download
        if download_canceler.has_active_download(user_id):
            await update.message.reply_text(
                "⚠️ **Download Already In Progress**\n\n"
                "You already have an active download running.\n\n"
                "**Options:**\n"
                "• Wait for current download to finish\n"
                "• Use `/cancel` to stop current download\n"
                "• Check `/stats` for current status\n\n"
                "🎯 Only one download per user is allowed at a time.",
                parse_mode='Markdown'
            )
            return
        
        logger.info(f"📥 New download request from user {user_id}: {text}")
        
        # Validate Terabox link
        text_lower = text.lower()
        supported_domains = [
            'terabox.com', '1024terabox.com', 'teraboxurl.com', 
            '4funbox.com', 'mirrobox.com', 'nephobox.com'
        ]
        
        is_valid = any(domain in text_lower for domain in supported_domains)
        
        if not is_valid:
            domain_list = '\n'.join([f"• {domain}" for domain in supported_domains])
            await update.message.reply_text(
                f"❌ **Invalid Terabox Link**\n\n"
                f"Please send a valid Terabox link.\n\n"
                f"**Supported domains:**\n{domain_list}\n\n"
                f"**Example:**\n`https://terabox.com/s/xxxxx`\n\n"
                f"💡 Make sure your link is complete and accessible!",
                parse_mode='Markdown'
            )
            return
        
        # Create initial status message
        status_msg = await update.message.reply_text(
            f"📥 **Processing Terabox Link**\n\n"
            f"🔗 `{text[:60]}{'...' if len(text) > 60 else ''}`\n"
            f"⏳ Connecting to download servers...\n"
            f"🔍 Extracting file information...\n\n"
            f"💡 Use `/cancel` to stop this download anytime",
            parse_mode='Markdown'
        )
        
        # Create and start download task
        task = asyncio.create_task(
            self._download_process(update, text, status_msg, user_id)
        )
        
        # Register download with canceler
        download_canceler.add_download(user_id, task, status_msg)
        
        try:
            # Wait for task completion
            await task
        except asyncio.CancelledError:
            logger.info(f"📋 Download task cancelled by user {user_id}")
        except Exception as e:
            logger.error(f"Download task error for user {user_id}: {e}")
        finally:
            # Always clean up
            download_canceler.remove_download(user_id)
    
    async def _download_process(self, update: Update, text: str, status_msg, user_id: int):
        """Complete download process with all features"""
        try:
            # Step 1: Get download information from API
            logger.info(f"🔍 Getting download info for user {user_id}")
            download_info = await self.downloader.get_download_info(text, status_msg)
            
            # Check if cancelled during API call
            if download_canceler.is_cancelled(user_id):
                logger.info(f"❌ Download cancelled during API call for user {user_id}")
                return
            
            if not download_info['success']:
                await status_msg.edit_text(
                    f"❌ **Download Info Failed**\n\n"
                    f"**Reason:** {download_info['error']}\n\n"
                    f"**💡 Possible solutions:**\n"
                    f"• Check if the link is valid and accessible\n"
                    f"• Try again in a few minutes\n"
                    f"• Use a different Terabox link\n"
                    f"• Make sure the file is still available\n\n"
                    f"🆘 If problem persists, contact support.",
                    parse_mode='Markdown'
                )
                return
            
            logger.info(f"✅ Got download info for user {user_id}: {download_info['filename']}")
            
            # Step 2: Detect media type and validate file
            file_ext = download_info['filename'].lower().split('.')[-1] if '.' in download_info['filename'] else ''
            media_type, media_emoji = self._detect_media_type(file_ext)
            
            # Check file size against limits
            try:
                size_mb = float(download_info['size'].replace('MB', '').replace('GB', '').replace('KB', '').strip())
                if 'GB' in download_info['size'] and size_mb > (config.MAX_FILE_SIZE // (1024*1024*1024)):
                    await status_msg.edit_text(
                        f"❌ **File Too Large**\n\n"
                        f"📁 **File:** {download_info['filename'][:40]}...\n"
                        f"💾 **Size:** {download_info['size']}\n"
                        f"📏 **Limit:** {config.MAX_FILE_SIZE // (1024*1024)}MB\n\n"
                        f"Please try a smaller file.",
                        parse_mode='Markdown'
                    )
                    return
            except:
                pass  # Skip size check if parsing fails
            
            # Step 3: Start file download
            await status_msg.edit_text(
                f"📥 **Downloading File**\n\n"
                f"📁 **File:** {download_info['filename'][:40]}{'...' if len(download_info['filename']) > 40 else ''}\n"
                f"💾 **Size:** {download_info['size']}\n"
                f"📱 **Type:** {media_emoji} {media_type}\n"
                f"⏳ **Status:** Starting download...\n\n"
                f"💡 This may take a while for large files\n"
                f"🚫 Use `/cancel` to stop",
                parse_mode='Markdown'
            )
            
            file_path = await self.downloader.download_file(
                download_info['download_url'],
                download_info['filename'],
                status_msg
            )
            
            # Check if cancelled during download
            if download_canceler.is_cancelled(user_id):
                logger.info(f"❌ Download cancelled during file download for user {user_id}")
                return
            
            if not file_path:
                await status_msg.edit_text(
                    f"❌ **File Download Failed**\n\n"
                    f"The file could not be downloaded from Terabox servers.\n\n"
                    f"**Possible reasons:**\n"
                    f"• File is too large (timeout)\n"
                    f"• Terabox servers are slow/down\n"
                    f"• Network connectivity issues\n"
                    f"• File link expired\n\n"
                    f"🔄 Please try again later!",
                    parse_mode='Markdown'
                )
                return
            
            logger.info(f"✅ File downloaded successfully for user {user_id}: {file_path}")
            
            # Update file path in canceler for cleanup
            if user_id in download_canceler.active_downloads:
                download_canceler.active_downloads[user_id]['file_path'] = file_path
            
            # Step 4: Upload to Telegram
            await status_msg.edit_text(
                f"📤 **Uploading to Telegram**\n\n"
                f"📁 **File:** {download_info['filename'][:40]}{'...' if len(download_info['filename']) > 40 else ''}\n"
                f"💾 **Size:** {download_info['size']}\n"
                f"📱 **Uploading as:** {media_emoji} {media_type}\n"
                f"⏳ **Status:** Preparing upload...\n\n"
                f"🚀 Almost done!",
                parse_mode='Markdown'
            )
            
            upload_success = await self.uploader.upload_with_progress(
                update, file_path, download_info['filename'], status_msg
            )
            
            if upload_success:
                # Success message
                await status_msg.edit_text(
                    f"🎉 **DOWNLOAD COMPLETE!**\n\n"
                    f"📁 **File:** {download_info['filename'][:40]}{'...' if len(download_info['filename']) > 40 else ''}\n"
                    f"💾 **Size:** {download_info['size']}\n"
                    f"📱 **Type:** {media_emoji} {media_type}\n"
                    f"⚡ **Status:** ✅ Successfully Uploaded\n\n"
                    f"✨ **Ready to view/play in Telegram!**\n"
                    f"🙏 Thank you for using {config.BOT_NAME}!",
                    parse_mode='Markdown'
                )
                logger.info(f"🎉 Complete success for user {user_id}: {media_type} upload")
            else:
                await status_msg.edit_text(
                    f"❌ **Upload Failed**\n\n"
                    f"File was downloaded but couldn't be uploaded to Telegram.\n\n"
                    f"**Possible reasons:**\n"
                    f"• File exceeds Telegram's 50MB limit\n"
                    f"• Invalid file format\n"
                    f"• Telegram server issues\n"
                    f"• File corrupted during download\n\n"
                    f"🔄 Please try again with a smaller file!",
                    parse_mode='Markdown'
                )
            
            # Step 5: Cleanup
            await self.downloader.cleanup_file(file_path)
            logger.info(f"🧹 Cleanup completed for user {user_id}")
                
        except Exception as e:
            logger.error(f"Download process error for user {user_id}: {e}")
            if not download_canceler.is_cancelled(user_id):
                await status_msg.edit_text(
                    f"❌ **System Error**\n\n"
                    f"An unexpected error occurred during processing.\n\n"
                    f"**Error details logged for debugging.**\n\n"
                    f"🔄 Please try again in a moment!\n"
                    f"🆘 If problem persists, contact support.\n\n"
                    f"📊 Check `/stats` for bot status.",
                    parse_mode='Markdown'
                )
    
    def _detect_media_type(self, file_ext: str):
        """Enhanced media type detection"""
        file_ext = file_ext.lower()
        
        # Comprehensive extension lists
        video_exts = [
            'mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv', '3gp', 'webm', 
            'm4v', 'mpg', 'mpeg', 'ogv', 'ts', 'vob', 'asf', 'rm', 'rmvb',
            'divx', 'xvid', 'h264', 'h265', 'hevc'
        ]
        
        audio_exts = [
            'mp3', 'wav', 'flac', 'aac', 'ogg', 'wma', 'm4a', 'opus', 
            'aiff', 'au', 'ra', 'amr', '3ga', 'ac3', 'dts', 'ape', 'alac'
        ]
        
        photo_exts = [
            'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'tiff', 'tif', 
            'svg', 'ico', 'heic', 'heif', 'raw', 'cr2', 'nef', 'arw'
        ]
        
        document_exts = [
            'pdf', 'doc', 'docx', 'xls', 'xlsx', 'ppt', 'pptx', 'txt', 
            'rtf', 'odt', 'ods', 'odp', 'zip', 'rar', '7z', 'tar', 'gz'
        ]
        
        if file_ext in video_exts:
            return "Video", "🎬"
        elif file_ext in audio_exts:
            return "Audio", "🎵"
        elif file_ext in photo_exts:
            return "Photo", "📸"
        elif file_ext in document_exts:
            return "Document", "📁"
        else:
            return "File", "📄"
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular text messages"""
        # Check force subscription first
        if config.ENABLE_FORCE_SUB and not await force_subscription.check_subscription(update, context):
            return
        
        user_id = update.effective_user.id
        active_downloads = len(download_canceler.active_downloads)
        user_has_download = download_canceler.has_active_download(user_id)
        
        await update.message.reply_text(
            f"ℹ️ **Send me a Terabox link!**\n\n"
            f"**📝 Supported formats:**\n"
            f"• `https://terabox.com/s/xxxxx`\n"
            f"• `https://1024terabox.com/s/xxxxx`\n"
            f"• `https://teraboxurl.com/s/xxxxx`\n"
            f"• And more Terabox domains\n\n"
            f"🎯 **What I'll do:**\n"
            f"1. **Detect** your file type automatically\n"
            f"2. **Download** from Terabox servers\n"
            f"3. **Upload** as proper media type to Telegram\n\n"
            f"📱 **Media types I support:**\n"
            f"🎬 Videos → Playable videos\n"
            f"🎵 Audio → Music files\n"
            f"📸 Photos → Viewable images\n"
            f"📁 Documents → File downloads\n\n"
            f"📊 **Current status:**\n"
            f"🔥 Active downloads: {active_downloads}\n"
            f"📥 Your status: {'⏳ Busy' if user_has_download else '✅ Ready'}\n\n"
            f"💡 Use `/help` for detailed guide or `/cancel` to stop downloads!",
            parse_mode='Markdown'
        )
