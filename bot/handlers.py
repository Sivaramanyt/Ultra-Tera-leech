"""
Bot handlers for commands and messages
"""
import asyncio
from loguru import logger
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from terabox.downloader import TeraboxDownloader
from verification.manager import VerificationManager
from utils.helpers import is_owner, is_authorized, extract_terabox_url
from messages.templates import MessageTemplates
import config

class BotHandlers:
    def __init__(self):
        self.downloader = TeraboxDownloader()
        self.verification = VerificationManager() if config.VERIFICATION_ENABLED else None
        self.templates = MessageTemplates()
        self.active_downloads = {}
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start"""
        user = update.effective_user
        logger.info(f"Start command from {user.id}")
        
        await update.message.reply_text(
            self.templates.welcome_message(user.first_name),
            parse_mode=ParseMode.HTML
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help"""
        await update.message.reply_text(
            self.templates.help_message(),
            parse_mode=ParseMode.HTML
        )
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats - Owner only"""
        if not is_owner(update.effective_user.id):
            await update.message.reply_text("❌ Owner only command")
            return
        
        stats = {
            'active_downloads': len(self.active_downloads),
            'verification_enabled': config.VERIFICATION_ENABLED,
            'bot_name': config.BOT_NAME
        }
        
        await update.message.reply_text(
            self.templates.stats_message(stats),
            parse_mode=ParseMode.HTML
        )
    
    async def verify_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /verify"""
        if not config.VERIFICATION_ENABLED:
            await update.message.reply_text("❌ Verification disabled")
            return
        
        user_id = update.effective_user.id
        
        if len(context.args) == 1:
            token = context.args[0]
            success, message = await self.verification.verify_token(token, user_id)
            
            if success:
                await update.message.reply_text(config.VERIFY_SUCCESS_MSG)
            else:
                await update.message.reply_text(f"{config.ERROR_PREFIX} {message}")
        else:
            await update.message.reply_text("❌ Usage: /verify <token>")
    
    async def handle_terabox_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle Terabox links"""
        user_id = update.effective_user.id
        
        if not is_authorized(user_id):
            await update.message.reply_text("❌ Not authorized")
            return
        
        if user_id in self.active_downloads:
            await update.message.reply_text("⏳ You have an active download")
            return
        
        # Check verification
        if config.VERIFICATION_ENABLED and await self.verification.need_verification(user_id):
            await self._request_verification(update, context)
            return
        
        # Extract URL
        terabox_url = extract_terabox_url(update.message.text)
        if not terabox_url:
            await update.message.reply_text("❌ Invalid Terabox link")
            return
        
        # Start download
        await self._process_download(update, context, terabox_url)
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages"""
        await update.message.reply_text(
            "ℹ️ Send me a Terabox link to download!\n\n"
            "Supported: terabox.com, 1024tera.com, 4funbox.com, mirrobox.com"
        )
    
    async def _request_verification(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Request verification"""
        user_id = update.effective_user.id
        
        try:
            verification_data = await self.verification.generate_verification(user_id)
            
            if verification_data:
                keyboard = [[InlineKeyboardButton("🔐 Verify", url=verification_data['short_url'])]]
                reply_markup = InlineKeyboardMarkup(keyboard)
                
                message = (
                    f"{config.VERIFY_MSG}\n\n"
                    f"⏰ Valid for: {config.VERIFY_VALIDITY_TIME//60} minutes\n"
                    f"🎯 Downloads used: {await self.verification.get_user_downloads(user_id)}/{config.FREE_LEECH_COUNT}"
                )
                
                await update.message.reply_text(message, reply_markup=reply_markup)
            else:
                await update.message.reply_text(f"{config.ERROR_PREFIX} Verification failed")
                
        except Exception as e:
            logger.error(f"Verification error: {e}")
            await update.message.reply_text(f"{config.ERROR_PREFIX} System error")
    
    async def _process_download(self, update: Update, context: ContextTypes.DEFAULT_TYPE, url: str):
        """Process download"""
        user_id = update.effective_user.id
        
        try:
            self.active_downloads[user_id] = True
            
            # Initial message
            status_msg = await update.message.reply_text(
                f"{config.PROGRESS_PREFIX} from Terabox...\n🔗 {url[:50]}..."
            )
            
            # Progress callback
            async def progress_callback(current, total, speed, eta):
                try:
                    progress = (current / total) * 100 if total > 0 else 0
                    bar = "█" * int(progress/10) + "░" * (10 - int(progress/10))
                    
                    text = (
                        f"{config.PROGRESS_PREFIX}\n"
                        f"📊 {progress:.1f}%\n"
                        f"[{bar}]\n"
                        f"⚡ {speed}\n"
                        f"⏱️ {eta}"
                    )
                    await status_msg.edit_text(text)
                except:
                    pass
            
            # Download
            result = await self.downloader.download_file(url, progress_callback)
            
            if result['success']:
                await status_msg.edit_text(f"{config.UPLOAD_PREFIX} to Telegram...")
                
                # Upload
                upload_result = await self._upload_file(update, context, result['file_path'], result['filename'])
                
                if upload_result:
                    await status_msg.edit_text(
                        f"{config.SUCCESS_PREFIX}\n"
                        f"📄 {result['filename']}\n"
                        f"💾 {result.get('size', 'Unknown')}"
                    )
                    
                    # Update count
                    if config.VERIFICATION_ENABLED:
                        await self.verification.increment_user_downloads(user_id)
                else:
                    await status_msg.edit_text(f"{config.ERROR_PREFIX} Upload failed")
            else:
                await status_msg.edit_text(f"{config.ERROR_PREFIX} {result.get('error', 'Download failed')}")
        
        except Exception as e:
            logger.error(f"Download error: {e}")
            await update.message.reply_text(f"{config.ERROR_PREFIX} {str(e)}")
        
        finally:
            if user_id in self.active_downloads:
                del self.active_downloads[user_id]
    
    async def _upload_file(self, update: Update, context: ContextTypes.DEFAULT_TYPE, file_path: str, filename: str):
        """Upload file to Telegram"""
        try:
            with open(file_path, 'rb') as file:
                if config.AS_DOCUMENT:
                    sent_msg = await update.message.reply_document(
                        document=file,
                        filename=filename,
                        caption=f"📄 {filename}\n\nBy {config.BOT_NAME}"
                    )
                else:
                    sent_msg = await update.message.reply_video(
                        video=file,
                        filename=filename,
                        caption=f"🎥 {filename}\n\nBy {config.BOT_NAME}"
                    )
            
            # Auto-forward
            if config.AUTO_FORWARD_ENABLED and config.LEECH_LOG_CHANNEL:
                try:
                    if config.FORWARD_TAGS:
                        user = update.effective_user
                        caption = f"📤 From [{user.first_name}](tg://user?id={user.id})"
                        await sent_msg.copy(config.LEECH_LOG_CHANNEL, caption=caption, parse_mode=ParseMode.MARKDOWN)
                    else:
                        await sent_msg.forward(config.LEECH_LOG_CHANNEL)
                except Exception as e:
                    logger.error(f"Forward error: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Upload error: {e}")
            return False
