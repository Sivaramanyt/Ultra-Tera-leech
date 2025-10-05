"""
Download functionality - Correct Working Version
"""
import aiohttp
import asyncio
import aiofiles
import os
from loguru import logger
import config

class TeraboxDownloader:
    def __init__(self):
        self.session = None
    
    async def get_session(self):
        """Simple session like your working bot"""
        if not self.session or self.session.closed:
            # Simple connector - don't overcomplicate
            connector = aiohttp.TCPConnector(
                limit=100,
                limit_per_host=30,
                force_close=True,
                enable_cleanup_closed=True
            )
            
            # Simple timeout
            timeout = aiohttp.ClientTimeout(
                total=None,  # No total timeout
                connect=30,
                sock_read=None  # No read timeout
            )
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Linux; Android 10; SM-G973F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.198 Mobile Safari/537.36'
                }
            )
        return self.session
    
    async def get_download_info(self, url: str, status_msg):
        """WDZone API - exactly like your working bot"""
        try:
            session = await self.get_session()
            api_url = 'https://wdzone-terabox-api.vercel.app/api'
            
            async with session.get(api_url, params={'url': url}) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    # Find the emoji keys (WDZone uses emoji keys)
                    status_key = None
                    info_key = None
                    
                    for key in result.keys():
                        if 'Status' in key:  # Look for "✅ Status"
                            status_key = key
                        if 'Info' in key:   # Look for "📜 Extracted Info"
                            info_key = key
                    
                    if status_key and info_key and result.get(status_key) == 'Success':
                        extracted_info = result.get(info_key)
                        
                        if isinstance(extracted_info, list) and len(extracted_info) > 0:
                            info = extracted_info[0]
                            
                            # Extract file information
                            download_url = None
                            filename = 'download.mp4'
                            size = 'Unknown'
                            
                            for key, value in info.items():
                                if isinstance(value, str):
                                    if 'Download' in key and value.startswith('https://'):  # "🔽 Direct Download Link"
                                        download_url = value
                                    elif 'Title' in key:  # "📂 Title"
                                        filename = value
                                    elif 'Size' in key:   # "📏 Size"
                                        size = value
                            
                            if download_url:
                                logger.info(f"✅ WDZone API Success - File: {filename}, Size: {size}")
                                return {
                                    'success': True,
                                    'download_url': download_url,
                                    'filename': filename,
                                    'size': size
                                }
            
            return {'success': False, 'error': 'No download URL found'}
            
        except Exception as e:
            logger.error(f"WDZone API Error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def download_file(self, download_url: str, filename: str, status_msg):
        """Simple working download like your other bot"""
        try:
            filename = self._sanitize_filename(filename)
            file_path = os.path.join(config.DOWNLOAD_DIR, filename)
            os.makedirs(config.DOWNLOAD_DIR, exist_ok=True)
            
            await status_msg.edit_text("📥 Downloading...", parse_mode=None)
            
            # Use the same session
            session = await self.get_session()
            
            async with session.get(download_url) as response:
                logger.info(f"Download response status: {response.status}")
                
                if response.status == 200:
                    total_size = int(response.headers.get('content-length', 0))
                    downloaded = 0
                    last_update = 0
                    
                    # Simple 1MB chunks like working bots use
                    async with aiofiles.open(file_path, 'wb') as file:
                        async for chunk in response.content.iter_chunked(1024*1024):  # 1MB chunks
                            await file.write(chunk)
                            downloaded += len(chunk)
                            
                            # Update every 2MB
                            if downloaded - last_update >= 2*1024*1024 or downloaded >= total_size:
                                last_update = downloaded
                                if total_size > 0:
                                    progress = (downloaded / total_size) * 100
                                    try:
                                        await status_msg.edit_text(
                                            f"📥 Downloading\n\n"
                                            f"Progress: {progress:.1f}%\n"
                                            f"Downloaded: {self._format_bytes(downloaded)}\n"
                                            f"Total: {self._format_bytes(total_size)}",
                                            parse_mode=None
                                        )
                                    except:
                                        pass
                    
                    # Simple verification
                    if os.path.exists(file_path):
                        final_size = os.path.getsize(file_path)
                        logger.info(f"✅ Download completed: {final_size} bytes")
                        return file_path
                    
                return None
            
        except Exception as e:
            logger.error(f"Download error: {e}")
            return None
    
    def _sanitize_filename(self, filename: str) -> str:
        """Clean filename"""
        import re
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        return filename[:200] if len(filename) > 200 else filename
    
    def _format_bytes(self, bytes_count: int) -> str:
        """Format bytes"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if bytes_count < 1024.0:
                return f"{bytes_count:.1f} {unit}"
            bytes_count /= 1024.0
        return f"{bytes_count:.1f} TB"
    
    async def cleanup_file(self, file_path: str):
        """Clean up file"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except:
            pass
    
    async def close(self):
        """Close session"""
        if self.session:
            await self.session.close()
                                    
