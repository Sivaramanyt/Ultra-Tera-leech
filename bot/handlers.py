"""
Bot handlers - Complete Version with Real Download & Upload
"""
import aiohttp
import asyncio
import aiofiles
import os
from loguru import logger
from telegram import Update
from telegram.ext import ContextTypes
import config

class BotHandlers:
    def __init__(self):
        pass
    
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
        """Handle Terabox links with real download and upload"""
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
            # Step 1: Get download URL from API
            download_result = await self._get_download_info(text, status_msg)
            
            if not download_result['success']:
                await status_msg.edit_text(
                    f"❌ Failed to get download info\n\n"
                    f"Reason: {download_result['error']}"
                )
                return
            
            # Step 2: Download the actual file
            file_path = await self._download_file(
                download_result['download_url'],
                download_result['filename'],
                status_msg
            )
            
            if not file_path:
                await status_msg.edit_text("❌ File download failed")
                return
            
            # Step 3: Upload to Telegram
            await status_msg.edit_text("📤 Uploading to Telegram...")
            
            upload_success = await self._upload_to_telegram(
                update, file_path, download_result['filename']
            )
            
            if upload_success:
                await status_msg.edit_text(
                    f"🎉 SUCCESS!\n\n"
                    f"📁 File: {download_result['filename']}\n"
                    f"💾 Size: {download_result['size']}\n"
                    f"⚡ Status: Uploaded to Telegram\n\n"
                    f"✨ Download complete!"
                )
            else:
                await status_msg.edit_text("❌ Upload to Telegram failed")
            
            # Clean up downloaded file
            await self._cleanup_file(file_path)
                
        except Exception as e:
            logger.error(f"Download process error: {e}")
            await status_msg.edit_text(
                "❌ System Error\n\n"
                "Something went wrong. Please try again!"
            )
    
    async def _get_download_info(self, url: str, status_msg):
        """Get download URL and file info from API"""
        try:
            # API endpoints
            api_endpoints = [
                {
                    'url': 'https://wdzone-terabox-api.vercel.app/api',
                    'type': 'wdzone'
                },
                {
                    'url': 'https://terabox-dl.qtcloud.workers.dev/',
                    'type': 'qtcloud'
                }
            ]
            
            for i, api_config in enumerate(api_endpoints):
                try:
                    await status_msg.edit_text(
                        f"📡 Getting download info...\n\n"
                        f"🔄 Server {i+1}/{len(api_endpoints)}\n"
                        f"⚡ Please wait..."
                    )
                    
                    result = await self._try_api_download(api_config, url)
                    
                    if result['success']:
                        logger.info(f"✅ Got download info from: {api_config['url']}")
                        return result
                        
                except Exception as e:
                    logger.warning(f"API {api_config['url']} failed: {e}")
                    continue
            
            return {'success': False, 'error': 'All APIs failed'}
            
        except Exception as e:
            return {'success': False, 'error': f'System error: {str(e)}'}
    
    async def _try_api_download(self, api_config: dict, terabox_url: str):
        """Try API to get download info"""
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                
                api_url = api_config['url']
                api_type = api_config['type']
                
                if api_type == 'wdzone':
                    params = {'url': terabox_url}
                    async with session.get(api_url, params=params) as response:
                        if response.status == 200:
                            result = await response.json()
                            
                            # Find status and info fields
                            status_field = None
                            info_field = None
                            
                            for key in result.keys():
                                if 'status' in key.lower():
                                    status_field = key
                                if 'info' in key.lower():
                                    info_field = key
                            
                            if status_field and info_field and result.get(status_field) == 'Success':
                                extracted_info = result.get(info_field)
                                if isinstance(extracted_info, list) and len(extracted_info) > 0:
                                    info = extracted_info[0]
                                    
                                    # Extract download info
                                    download_url = None
                                    title = 'download'
                                    size = 'Unknown'
                                    
                                    for key in info.keys():
                                        if 'download' in key.lower():
                                            download_url = info.get(key)
                                        if 'title' in key.lower() or 'name' in key.lower():
                                            title = info.get(key, 'download')
                                        if 'size' in key.lower():
                                            size = info.get(key, 'Unknown')
                                    
                                    if download_url:
                                        return {
                                            'success': True,
                                            'download_url': download_url,
                                            'filename': title,
                                            'size': size
                                        }
                
                elif api_type == 'qtcloud':
                    params = {'url': terabox_url}
                    async with session.get(api_url, params=params) as response:
                        if response.status == 200:
                            result = await response.json()
                            
                            if result.get('download'):
                                return {
                                    'success': True,
                                    'download_url': result['download'],
                                    'filename': result.get('name', 'download'),
                                    'size': result.get('size', 'Unknown')
                                }
            
            return {'success': False, 'error': 'No download URL found'}
            
        except Exception as e:
            return {'success': False, 'error': f'API error: {str(e)}'}
    
    async def _download_file(self, download_url: str, filename: str, status_msg):
        """Download the actual file from direct URL"""
        try:
            # Sanitize filename
            filename = self._sanitize_filename(filename)
            file_path = os.path.join(config.DOWNLOAD_DIR, filename)
            
            # Make sure download directory exists
            os.makedirs(config.DOWNLOAD_DIR, exist_ok=True)
            
            logger.info(f"📥 Downloading file to: {file_path}")
            
            timeout = aiohttp.ClientTimeout(total=300)  # 5 minutes
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(download_url) as response:
                    if response.status == 200:
                        total_size = int(response.headers.get('content-length', 0))
                        downloaded = 0
                        
                        async with aiofiles.open(file_path, 'wb') as file:
                            async for chunk in response.content.iter_chunked(8192):
                                await file.write(chunk)
                                downloaded += len(chunk)
                                
                                # Update progress every 1MB
                                if downloaded % (1024 * 1024) == 0 or downloaded >= total_size:
                                    if total_size > 0:
                                        progress = (downloaded / total_size) * 100
                                        await status_msg.edit_text(
                                            f"📥 Downloading file...\n\n"
                                            f"📊 Progress: {progress:.1f}%\n"
                                            f"💾 Downloaded: {self._format_bytes(downloaded)}\n"
                                            f"📦 Total: {self._format_bytes(total_size)}"
                                        )
                        
                        logger.info(f"✅ File downloaded successfully: {file_path}")
                        return file_path
                    else:
                        logger.error(f"❌ Download failed: HTTP {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"Download error: {e}")
            return None
    
    async def _upload_to_telegram(self, update: Update, file_path: str, filename: str):
        """Upload file to Telegram"""
        try:
            logger.info(f"📤 Uploading to Telegram: {file_path}")
            
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
            return False
    
    def _sanitize_filename(self, filename: str) -> str:
        """Clean filename for safe storage"""
        import re
        # Remove invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Limit length
        if len(filename) > 200:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            filename = name[:200-len(ext)-1] + '.' + ext if ext else name[:200]
        return filename
    
    def _format_bytes(self, bytes_count: int) -> str:
        """Format bytes to human readable"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_count < 1024.0:
                return f"{bytes_count:.1f} {unit}"
            bytes_count /= 1024.0
        return f"{bytes_count:.1f} TB"
    
    async def _cleanup_file(self, file_path: str):
        """Clean up downloaded file"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"🧹 Cleaned up: {file_path}")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular text"""
        await update.message.reply_text(
            "ℹ️ Send me a Terabox link!\n\n"
            "Examples:\n"
            "• https://terabox.com/s/xxxxx\n"
            "• https://1024terabox.com/s/xxxxx\n\n"
            "I'll download it for you! 🚀"
                )
                
