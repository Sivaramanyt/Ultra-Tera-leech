"""
Cancel functionality for ongoing downloads
"""
import asyncio
from loguru import logger
from telegram import Update
from telegram.ext import ContextTypes

class DownloadCanceler:
    def __init__(self):
        self.active_downloads = {}  # user_id: {task, status_msg, file_path}
    
    def add_download(self, user_id: int, task, status_msg, file_path=None):
        """Add active download for user"""
        self.active_downloads[user_id] = {
            'task': task,
            'status_msg': status_msg,
            'file_path': file_path,
            'cancelled': False
        }
        logger.info(f"📋 Added download task for user {user_id}")
    
    def remove_download(self, user_id: int):
        """Remove completed/cancelled download"""
        if user_id in self.active_downloads:
            del self.active_downloads[user_id]
            logger.info(f"🗑️ Removed download task for user {user_id}")
    
    async def cancel_download(self, user_id: int):
        """Cancel user's active download"""
        if user_id not in self.active_downloads:
            return False
        
        download_info = self.active_downloads[user_id]
        
        # Mark as cancelled
        download_info['cancelled'] = True
        
        # Cancel the asyncio task
        if download_info['task'] and not download_info['task'].done():
            download_info['task'].cancel()
            logger.info(f"❌ Cancelled download task for user {user_id}")
        
        # Clean up file if exists
        if download_info.get('file_path'):
            try:
                import os
                if os.path.exists(download_info['file_path']):
                    os.remove(download_info['file_path'])
                    logger.info(f"🧹 Cleaned up file: {download_info['file_path']}")
            except Exception as e:
                logger.error(f"Cleanup error: {e}")
        
        # Update status message
        try:
            await download_info['status_msg'].edit_text(
                "❌ **Download Cancelled**\n\n"
                "The download has been cancelled by user.\n"
                "You can start a new download anytime!",
                parse_mode='Markdown'
            )
        except:
            pass
        
        # Remove from active downloads
        self.remove_download(user_id)
        return True
    
    def has_active_download(self, user_id: int):
        """Check if user has active download"""
        return user_id in self.active_downloads
    
    def is_cancelled(self, user_id: int):
        """Check if download is cancelled"""
        if user_id not in self.active_downloads:
            return False
        return self.active_downloads[user_id].get('cancelled', False)

# Global instance
download_canceler = DownloadCanceler()
