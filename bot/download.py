"""
Download functionality - Original Working Version (Markdown Safe)
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
        """Get basic HTTP session"""
        if not self.session or self.session.closed:
            connector = aiohttp.TCPConnector()
            timeout = aiohttp.ClientTimeout(total=300)
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
        return self.session
    
    async def get_download_info(self, url: str, status_msg):
        """Get download URL from WDZone API - Original Working Version"""
        try:
            session = await self.get_session()
            api_url = 'https://wdzone-terabox-api.vercel.app/api'
            params = {'url': url}
            
            async with session.get(api_url, params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    # Original working logic - look for status and info fields
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
                            
                            # Extract file information
                            download_url = None
                            filename = 'download'
                            size = 'Unknown'
                            
                            for key, value in info.items():
                                if isinstance(value, str):
                                    if 'download' in key.lower() and value.startswith('https://'):
                                        download_url = value
                                    elif 'title' in key.lower():
                                        filename = value
                                    elif 'size' in key.lower():
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
            logger.error(f"API Error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def download_file(self, download_url: str, filename: str, status_msg):
        """Original working download method - Markdown Safe"""
        try:
            filename = self._sanitize_filename(filename)
            file_path = os.path.join(config.DOWNLOAD_DIR, filename)
            os.makedirs(config.DOWNLOAD_DIR, exist_ok=True)
            
            # Simple progress message - NO MARKDOWN
            await status_msg.edit_text("📥 Downloading...", parse_mode=None)
            
            session = await self.get_session()
            
            async with session.get(download_url, allow_redirects=True) as response:
                if response.status == 200:
                    total_size = int(response.headers.get('content-length', 0))
                    downloaded = 0
                    last_update = 0
                    start_time = asyncio.get_event_loop().time()
                    
                    # Original small chunks - STABLE
                    chunk_size = 8192  # 8KB chunks (original working size)
                    
                    async with aiofiles.open(file_path, 'wb') as file:
                        async for chunk in response.content.iter_chunked(chunk_size):
                            await file.write(chunk)
                            downloaded += len(chunk)
                            
                            # Original progress update interval - NO MARKDOWN
                            if downloaded - last_update >= 1048576 or downloaded >= total_size:  # Every 1MB
                                last_update = downloaded
                                current_time = asyncio.get_event_loop().time()
                                elapsed = current_time - start_time
                                
                                if total_size > 0 and elapsed > 0:
                                    progress = (downloaded / total_size) * 100
                                    speed = downloaded / elapsed
                                    speed_mb = speed / (1024 * 1024)
                                    
                                    try:
                                        await status_msg.edit_text(
                                            f"📥 Downloading...\n\n"
                                            f"📊 Progress: {progress:.1f}%\n"
                                            f"⚡ Speed: {speed_mb:.2f} MB/s",
                                            parse_mode=None  # NO MARKDOWN PARSING
                                        )
                                    except:
                                        pass
                    
                    # Verify download
                    if os.path.exists(file_path):
                        final_size = os.path.getsize(file_path)
                        if final_size > 0:
                            logger.info(f"✅ Download completed: {final_size} bytes")
                            return file_path
                    
                    return None
                else:
                    logger.error(f"Download failed: HTTP {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Download error: {e}")
            return None
    
    def _sanitize_filename(self, filename: str) -> str:
        """Clean filename"""
        import re
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        if len(filename) > 200:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            filename = name[:200-len(ext)-1] + '.' + ext if ext else name[:200]
        return filename
    
    async def cleanup_file(self, file_path: str):
        """Clean up file"""
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"🧹 Cleaned up: {file_path}")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
    
    async def close(self):
        """Close session"""
        if self.session:
            await self.session.close()
                            
