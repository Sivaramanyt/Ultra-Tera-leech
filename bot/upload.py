"""
Upload functionality for Telegram files - Media Type Upload
"""
import os
from loguru import logger
from telegram import Update
import config

class TelegramUploader:
    def __init__(self):
        pass
    
    async def upload_with_progress(self, update: Update, file_path: str, filename: str, status_msg):
        """Upload file as appropriate media type with progress updates"""
        try:
            await status_msg.edit_text("📤 Uploading to Telegram...")
            
            # Determine file type and upload accordingly
            file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
            file_size = os.path.getsize(file_path)
            
            logger.info(f"📤 Uploading {filename} as media type (ext: {file_ext}, size: {self._format_bytes(file_size)})")
            
            # Upload based on file type
            success = False
            
            if file_ext in self._get_video_extensions():
                success = await self.upload_as_video(update, file_path, filename)
            elif file_ext in self._get_audio_extensions():
                success = await self.upload_as_audio(update, file_path, filename)  
            elif file_ext in self._get_photo_extensions():
                success = await self.upload_as_photo(update, file_path, filename)
            else:
                # For unknown types, try as video first (most common), then document
                success = await self.upload_as_video(update, file_path, filename)
                if not success:
                    success = await self.upload_as_document(update, file_path, filename)
            
            return success
            
        except Exception as e:
            logger.error(f"Upload with progress error: {e}")
            return False
    
    async def upload_as_video(self, update: Update, file_path: str, filename: str):
        """Upload as video media"""
        try:
            file_size = os.path.getsize(file_path)
            
            if file_size > 50 * 1024 * 1024:  # 50MB limit
                await update.message.reply_text(
                    f"❌ Video too large: {self._format_bytes(file_size)}\n"
                    f"Telegram limit: 50MB"
                )
                return False
            
            with open(file_path, 'rb') as file:
                await update.message.reply_video(
                    video=file,
                    caption=f"🎬 {filename}\n💾 {self._format_bytes(file_size)}\n\n🤖 {config.BOT_NAME}",
                    supports_streaming=True
                )
            
            logger.info("✅ Video uploaded successfully")
            return True
            
        except Exception as e:
            logger.warning(f"Video upload failed: {e}")
            return False
    
    async def upload_as_audio(self, update: Update, file_path: str, filename: str):
        """Upload as audio media"""
        try:
            file_size = os.path.getsize(file_path)
            
            if file_size > 50 * 1024 * 1024:  # 50MB limit
                await update.message.reply_text(
                    f"❌ Audio too large: {self._format_bytes(file_size)}\n"
                    f"Telegram limit: 50MB"
                )
                return False
            
            with open(file_path, 'rb') as file:
                await update.message.reply_audio(
                    audio=file,
                    caption=f"🎵 {filename}\n💾 {self._format_bytes(file_size)}\n\n🤖 {config.BOT_NAME}",
                    title=filename
                )
            
            logger.info("✅ Audio uploaded successfully")
            return True
            
        except Exception as e:
            logger.warning(f"Audio upload failed: {e}")
            return False
    
    async def upload_as_photo(self, update: Update, file_path: str, filename: str):
        """Upload as photo media"""
        try:
            file_size = os.path.getsize(file_path)
            
            if file_size > 10 * 1024 * 1024:  # 10MB limit for photos
                logger.info("Photo too large, uploading as document")
                return await self.upload_as_document(update, file_path, filename)
            
            with open(file_path, 'rb') as file:
                await update.message.reply_photo(
                    photo=file,
                    caption=f"📸 {filename}\n💾 {self._format_bytes(file_size)}\n\n🤖 {config.BOT_NAME}"
                )
            
            logger.info("✅ Photo uploaded successfully")
            return True
            
        except Exception as e:
            logger.warning(f"Photo upload failed: {e}")
            return False
    
    async def upload_as_document(self, update: Update, file_path: str, filename: str):
        """Upload as document (fallback)"""
        try:
            file_size = os.path.getsize(file_path)
            
            if file_size > 50 * 1024 * 1024:  # 50MB limit
                await update.message.reply_text(
                    f"❌ File too large: {self._format_bytes(file_size)}\n"
                    f"Telegram limit: 50MB"
                )
                return False
            
            with open(file_path, 'rb') as file:
                await update.message.reply_document(
                    document=file,
                    filename=filename,
                    caption=f"📁 {filename}\n💾 {self._format_bytes(file_size)}\n\n🤖 {config.BOT_NAME}"
                )
            
            logger.info("✅ Document uploaded successfully")
            return True
            
        except Exception as e:
            logger.error(f"Document upload failed: {e}")
            return False
    
    def _get_video_extensions(self):
        """Get list of video file extensions"""
        return [
            'mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv', '3gp', 'webm', 
            'm4v', 'mpg', 'mpeg', 'ogv', 'ts', 'vob', 'asf', 'rm', 'rmvb'
        ]
    
    def _get_audio_extensions(self):
        """Get list of audio file extensions"""
        return [
            'mp3', 'wav', 'flac', 'aac', 'ogg', 'wma', 'm4a', 'opus', 
            'aiff', 'au', 'ra', 'amr', '3ga', 'ac3', 'dts'
        ]
    
    def _get_photo_extensions(self):
        """Get list of photo file extensions"""
        return [
            'jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp', 'tiff', 'tif', 
            'svg', 'ico', 'heic', 'heif'
        ]
    
    def _format_bytes(self, bytes_count: int) -> str:
        """Format bytes to human readable"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_count < 1024.0:
                return f"{bytes_count:.1f} {unit}"
            bytes_count /= 1024.0
        return f"{bytes_count:.1f} TB"
            
