"""
Download functionality - Bulletproof Raw Stream Version
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
        """Bulletproof session"""
        if not self.session or self.session.closed:
            # Minimal connector
            connector = aiohttp.TCPConnector(
                limit=50,
                limit_per_host=10
            )
            
            # No timeouts to prevent drops
            timeout = aiohttp.ClientTimeout(
                total=None,
                connect=60,
                sock_read=None
            )
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
        return self.session
    
    async def get_download_info(self, url: str, status_msg):
        """WDZone API"""
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
    
    async def download_file(self, download_url: str, filename: str, status_msg):
        """Bulletproof raw stream download"""
        try:
            filename = self._sanitize_filename(filename)
            file_path = os.path.join(config.DOWNLOAD_DIR, filename)
            os.makedirs(config.DOWNLOAD_DIR, exist_ok=True)
            
            await status_msg.edit_text("📥 Downloading...", parse_mode=None)
            
            session = await self.get_session()
            
            async with session.get(download_url) as response:
                logger.info(f"Download response status: {response.status}")
                
                if response.status == 200:
                    total_size = int(response.headers.get('content-length', 0))
                    downloaded = 0
                    
                    async with aiofiles.open(file_path, 'wb') as file:
                        # Raw byte reading instead of chunked
                        buffer_size = 65536  # 64KB buffer
                        
                        while True:
                            try:
                                # Read raw bytes directly
                                chunk = await response.content.read(buffer_size)
                                if not chunk:
                                    break
                                
                                await file.write(chunk)
                                downloaded += len(chunk)
                                
                                # Progress every 1MB
                                if downloaded % (1024*1024) == 0 or downloaded >= total_size:
                                    if total_size > 0:
                                        progress = (downloaded / total_size) * 100
                                        try:
                                            await status_msg.edit_text(
                                                f"📥 Downloading\n\n"
                                                f"Progress: {progress:.1f}%\n"
                                                f"Downloaded: {self._format_bytes(downloaded)}\n"
                                                f"Total: {self._format_bytes(total_size)}\n"
                                                f"Method: Raw stream",
                                                parse_mode=None
                                            )
                                        except:
                                            pass
                            
                            except asyncio.IncompleteReadError:
                                # Handle incomplete reads gracefully
                                logger.warning("Incomplete read, continuing...")
                                break
                            except Exception as e:
                                logger.error(f"Read error: {e}")
                                break
                    
                    # Verify
                    if os.path.exists(file_path):
                        final_size = os.path.getsize(file_path)
                        logger.info(f"✅ Download completed: {final_size} bytes")
                        
                        # Accept if we got at least 90% of the file
                        if total_size == 0 or final_size >= total_size * 0.9:
                            return file_path
                        else:
                            logger.warning(f"File incomplete: {final_size}/{total_size}")
                    
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
                    
