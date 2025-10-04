"""
Telegram upload utilities
"""
import os
from loguru import logger
from telegram import Document, Video
from telegram.error import TelegramError

async def upload_file(update, context, file_path: str, filename: str, as_document: bool = False):
    """Upload file to Telegram"""
    try:
        with open(file_path, 'rb') as file:
            if as_document:
                return await update.message.reply_document(
                    document=file,
                    filename=filename,
                    caption=f"📄 {filename}"
                )
            else:
                # Try as video first, fallback to document
                try:
                    return await update.message.reply_video(
                        video=file,
                        filename=filename,
                        caption=f"🎥 {filename}"
                    )
                except TelegramError:
                    # Fallback to document
                    file.seek(0)  # Reset file pointer
                    return await update.message.reply_document(
                        document=file,
                        filename=filename,
                        caption=f"📄 {filename}"
                    )
                    
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise

def cleanup_file(file_path: str):
    """Clean up downloaded file"""
    try:
        if os.path.exists(file_path):
            os.remove(file_path)
            logger.info(f"Cleaned up: {file_path}")
    except Exception as e:
        logger.error(f"Cleanup error: {e}")
