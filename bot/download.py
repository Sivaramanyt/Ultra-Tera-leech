"""
Download functionality - Sync Requests in Thread (Like Working Bots)
"""
import aiohttp
import asyncio
import aiofiles
import os
import requests
from concurrent.futures import ThreadPoolExecutor
from loguru import logger
import config

class TeraboxDownloader:
    def __init__(self):
        self.session = None
        self.executor = ThreadPoolExecutor(max_workers=2)
    
    async def get_session(self):
        """Session for API only"""
        if not self.session or self.session.closed:
            connector = aiohttp.TCPConnector()
            timeout = aiohttp.ClientTimeout(total=300)
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            )
        return self.session
    
    async def get_download_info(self, url: str, status_msg):
        """WDZone API with aiohttp"""
        try:
            session = await self.get_session()
            api_url = 'https://wdzone-terabox-api.vercel.app/api'
            
            async with session.get(api_url, params={'url': url}) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    # Find emoji keys
                    status_key = next((k for k in result.keys() if 'Status' in k), None)
                    info_key = next((k for k in result.keys() if 'Info' in k), None)
                    
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
                                    if 'Download' in key and value.startswith('https://'):
                                        download_url = value
                                    elif 'Title' in key:
                                        filename = value
                                    elif 'Size' in key:
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
    
    def _download_sync(self, download_url: str, file_path: str, status_callback):
        """Synchronous download with requests (like working bots)"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            # Use requests (sync) - this is what working bots use
            response = requests.get(download_url, headers=headers, stream=True, timeout=(30, None))
            
            if response.status_code == 200:
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                
                with open(file_path, 'wb') as file:
                    for chunk in response.iter_content(chunk_size=1024*1024):  # 1MB chunks
                        if chunk:
                            file.write(chunk)
                            downloaded += len(chunk)
                            
                            # Progress callback every 2MB
                            if downloaded % (2*1024*1024) == 0 or downloaded >= total_size:
                                if status_callback:
                                    progress = (downloaded / total_size) * 100 if total_size > 0 else 0
                                    status_callback(downloaded, total_size, progress)
                
                logger.info(f"✅ Sync download completed: {downloaded} bytes")
                return True
            else:
                logger.error(f"HTTP {response.status_code}")
                return False
                
        except Exception as e:
            logger.error(f"Sync download error: {e}")
            return False
    
    async def download_file(self, download_url: str, filename: str, status_msg):
        """Download using sync requests in thread"""
        try:
            filename = self._sanitize_filename(filename)
            file_path = os.path.join(config.DOWNLOAD_DIR, filename)
            os.makedirs(config.DOWNLOAD_DIR, exist_ok=True)
            
            await status_msg.edit_text("📥 Starting sync download...", parse_mode=None)
            
            # Progress update function
            last_update = [0]  # Use list for mutable reference
            
            def progress_callback(downloaded, total_size, progress):
                # Only update every 2MB to avoid spam
                if downloaded - last_update[0] >= 2*1024*1024:
                    last_update[0] = downloaded
                    # Schedule update on event loop
                    asyncio.create_task(status_msg.edit_text(
                        f"📥 Sync Download\n\n"
                        f"Progress: {progress:.1f}%\n"
                        f"Downloaded: {self._format_bytes(downloaded)}\n"
                        f"Total: {self._format_bytes(total_size)}\n"
                        f"Method: Requests (sync)",
                        parse_mode=None
                    ))
            
            # Run sync download in thread
            loop = asyncio.get_event_loop()
            success = await loop.run_in_executor(
                self.executor,
                self._download_sync,
                download_url,
                file_path,
                progress_callback
            )
            
            if success and os.path.exists(file_path):
                final_size = os.path.getsize(file_path)
                if final_size > 0:
                    logger.info(f"✅ Download successful: {final_size} bytes")
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
        """Close session and executor"""
        if self.session:
            await self.session.close()
        self.executor.shutdown(wait=False)
    
