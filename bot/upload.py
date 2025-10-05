"""
Upload functionality - High-Speed Version
"""
import os
from loguru import logger
from telegram import Update
from telegram.constants import ParseMode
import config

class TelegramUploader:
    def __init__(self):
        pass
    
    async def upload_with_progress(self, update: Update, file_path: str, filename: str, status_msg):
        """High-speed upload with optimizations"""
        try:
            await status_msg.edit_text(
                "📤 **High-Speed Upload Starting...**\n\n"
                "🚀 Optimized for maximum upload speed",
                parse_mode='Markdown'
            )
            
            # Determine file type and upload
            file_ext = filename.lower().split('.')[-1] if '.' in filename else ''
            file_size = os.path.getsize(file_path)
            
            logger.info(f"📤 High-speed upload: {filename} ({self._format_bytes(file_size)})")
            
            # Fast upload based on type
            success = False
            
            if file_ext in self._get_video_extensions():
                success = await self._upload_as_video_fast(update, file_path, filename)
            elif file_ext in self._get_audio_extensions():
                success = await self._upload_as_audio_fast(update, file_path, filename)  
            elif file_ext in self._get_photo_extensions():
                success = await self._upload_as_photo_fast(update, file_path, filename)
            else:
                success = await self._upload_as_document_fast(update, file_path, filename)
            
            return success
            
        except Exception as e:
            logger.error(f"High-speed upload error: {e}")
            return False
    
    async def _upload_as_video_fast(self, update: Update, file_path: str, filename: str):
        """Fast video upload"""
        try:
            file_size = os.path.getsize(file_path)
            
            if file_size > 50 * 1024 * 1024:  # 50MB limit
                await update.message.reply_text(
                    f"❌ Video too large: {self._format_bytes(file_size)}"
                )
                return False
            
            with open(file_path, 'rb') as file:
                await update.message.reply_video(
                    video=file,
                    caption=f"🎬 {filename}\n💾 {self._format_bytes(file_size)}\n🚀 High-Speed Upload",
                    supports_streaming=True,
                    read_timeout=300,  # 5 minutes
                    write_timeout=300,
                    connect_timeout=60
                )
            
            logger.info("✅ Fast video upload successful")
            return True
            
        except Exception as e:
            logger.warning(f"Fast video upload failed: {e}")
            return False
    
    async def _upload_as_audio_fast(self, update: Update, file_path: str, filename: str):
        """Fast audio upload"""
        try:
            file_size = os.path.getsize(file_path)
            
            with open(file_path, 'rb') as file:
                await update.message.reply_audio(
                    audio=file,
                    caption=f"🎵 {filename}\n💾 {self._format_bytes(file_size)}\n🚀 High-Speed Upload",
                    title=filename,
                    read_timeout=300,
                    write_timeout=300,
                    connect_timeout=60
                )
            
            return True
            
        except Exception as e:
            logger.warning(f"Fast audio upload failed: {e}")
            return False
    
    def _get_video_extensions(self):
        return ['mp4', 'avi', 'mkv', 'mov', 'wmv', 'flv', '3gp', 'webm', 'm4v']
    
    def _get_audio_extensions(self):
        return ['mp3', 'wav', 'flac', 'aac', 'ogg', 'wma', 'm4a', 'opus']
    
    def _get_photo_extensions(self):
        return ['jpg', 'jpeg', 'png', 'gif', 'bmp', 'webp']
    
    def _format_bytes(self, bytes_count: int) -> str:
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_count < 1024.0:
                return f"{bytes_count:.1f} {unit}"
            bytes_count /= 1024.0
        return f"{bytes_count:.1f} TB"
        
