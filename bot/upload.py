"""
Upload functionality for Telegram files
"""
import os
from loguru import logger
from telegram import Update
import config

class TelegramUploader:
    def __init__(self):
        pass
    
    async def upload_file(self, update: Update, file_path: str, filename: str):
        """Upload file to Telegram"""
        try:
            logger.info(f"📤 Uploading to Telegram: {file_path}")
            
            # Check file exists
            if not os.path.exists(file_path):
                logger.error(f"❌ File not found: {file_path}")
                return False
            
            # Check file size
            file_size = os.path.getsize(file_path)
            
            if file_size > 50 * 1024 * 1024:  # 50MB limit for bots
                await update.message.reply_text(
                    f"❌ File too large: {self._format_bytes(file_size)}\n"
                    f"Telegram bot limit: 50MB"
                )
                return False
            
            # Upload as document
            with open(file_path, 'rb') as file:
                await update.message.reply_document(
                    document=file,
                    filename=filename,
                    caption=f"📁 {filename}\n💾 Size: {self._format_bytes(file_size)}\n\n🤖 Downloaded by {config.BOT_NAME}"
                )
            
            logger.info("✅ File uploaded to Telegram successfully")
            return True
            
        except Exception as e:
            logger.error(f"Upload error: {e}")
            await update.message.reply_text(
                "❌ Upload Failed\n\n"
                "Could not upload file to Telegram.\n"
                "The file might be corrupted or too large."
            )
            return False
    
    async def upload_video(self, update: Update, file_path: str, filename: str):
        """Upload video file to Telegram"""
        try:
            file_size = os.path.getsize(file_path)
            
            if file_size > 50 * 1024 * 1024:
                return await self.upload_file(update, file_path, filename)
            
            # Try as video first
            with open(file_path, 'rb') as file:
                await update.message.reply_video(
                    video=file,
                    caption=f"🎬 {filename}\n💾 Size: {self._format_bytes(file_size)}\n\n🤖 Downloaded by {config.BOT_NAME}"
                )
            
            logger.info("✅ Video uploaded to Telegram successfully")
            return True
            
        except Exception as e:
            logger.warning(f"Video upload failed, trying as document: {e}")
            return await self.upload_file(update, file_path, filename)
    
    async def upload_with_progress(self, update: Update, file_path: str, filename: str, status_msg):
        """Upload file with progress updates"""
        try:
            await status_msg.edit_text("📤 Uploading to Telegram...")
            
            # Determine file type
            file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
            video_extensions = ['mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv', '3gp']
            
            if file_ext in video_extensions:
                success = await self.upload_video(update, file_path, filename)
            else:
                success = await self.upload_file(update, file_path, filename)
            
            return success
            
        except Exception as e:
            logger.error(f"Upload with progress error: {e}")
            return False
    
    def _format_bytes(self, bytes_count: int) -> str:
        """Format bytes to human readable"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_count < 1024.0:
                return f"{bytes_count:.1f} {unit}"
            bytes_count /= 1024.0
        return f"{bytes_count:.1f} TB"
