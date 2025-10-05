"""
Enhanced Download Module with Multiple Fallback Strategies
"""
import os
import asyncio
import aiohttp
import aiofiles
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential
import config

class TeraboxDownloader:
    def __init__(self):
        self.session = None
    
    async def get_session(self):
        """Get or create aiohttp session with optimized settings"""
        if self.session is None or self.session.closed:
            timeout = aiohttp.ClientTimeout(
                total=300,      # 5 minutes total
                connect=30,     # 30 seconds to connect
                sock_read=60    # 60 seconds between reads
            )
            
            connector = aiohttp.TCPConnector(
                limit=10,
                limit_per_host=5,
                keepalive_timeout=60,
                enable_cleanup_closed=True
            )
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
            )
        return self.session
    
    async def close_session(self):
        """Close aiohttp session"""
        if self.session and not self.session.closed:
            await self.session.close()
    
    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    async def get_download_info(self, terabox_url: str):
        """Get download information from API with retry"""
        api_url = f"https://wdzone-terabox-api.vercel.app/file_info?url={terabox_url}"
        
        session = await self.get_session()
        async with session.get(api_url) as response:
            if response.status == 200:
                data = await response.json()
                
                if data.get("ok") and data.get("file_info"):
                    file_info = data["file_info"]
                    file_name = file_info.get("file_name", "unknown_file")
                    file_size = file_info.get("size", 0)
                    download_url = file_info.get("download_url")
                    
                    if download_url:
                        # Convert size to MB for logging
                        size_mb = file_size / (1024 * 1024) if file_size else 0
                        logger.info(f"✅ WDZone API Success - File: {file_name}, Size: {size_mb:.2f} MB")
                        
                        return {
                            "file_name": file_name,
                            "file_size": file_size, 
                            "download_url": download_url
                        }
                
                logger.error(f"❌ API returned invalid data: {data}")
                raise Exception("Invalid API response")
            else:
                logger.error(f"❌ API request failed with status {response.status}")
                raise Exception(f"API request failed: {response.status}")
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe storage"""
        import re
        # Remove invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Limit length
        if len(filename) > 200:
            name, ext = os.path.splitext(filename)
            filename = name[:190] + ext
        return filename
    
    async def download_with_resume(self, download_url: str, filename: str, status_msg, max_retries=5):
        """Download with resume capability and multiple strategies"""
        filename = self._sanitize_filename(filename)
        file_path = os.path.join(config.DOWNLOAD_DIR, filename)
        os.makedirs(config.DOWNLOAD_DIR, exist_ok=True)
        
        # Try different download strategies
        strategies = [
            ("Direct Stream", self._direct_stream_download),
            ("Chunked Download", self._chunked_download), 
            ("Byte-by-byte", self._micro_download),
            ("Resume Download", self._resume_download)
        ]
        
        for strategy_name, strategy_func in strategies:
            try:
                await status_msg.edit_text(f"📥 Trying {strategy_name}...", parse_mode=None)
                logger.info(f"🔄 Attempting {strategy_name}")
                
                if await strategy_func(download_url, file_path):
                    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                        logger.info(f"✅ {strategy_name} successful!")
                        return file_path
                
                logger.warning(f"❌ {strategy_name} failed, trying next strategy...")
                
            except Exception as e:
                logger.error(f"❌ {strategy_name} error: {e}")
                continue
        
        # If all strategies fail, try one final attempt with maximum patience
        try:
            await status_msg.edit_text("📥 Final attempt with maximum patience...", parse_mode=None)
            if await self._patient_download(download_url, file_path):
                return file_path
        except Exception as e:
            logger.error(f"❌ Final patient download failed: {e}")
        
        return None
    
    async def _direct_stream_download(self, download_url: str, file_path: str) -> bool:
        """Direct stream download - fastest but may fail on large files"""
        try:
            session = await self.get_session()
            async with session.get(download_url) as response:
                if response.status == 200:
                    content = await response.read()
                    async with aiofiles.open(file_path, 'wb') as file:
                        await file.write(content)
                    return True
        except Exception as e:
            logger.warning(f"Direct stream failed: {e}")
        return False
    
    async def _chunked_download(self, download_url: str, file_path: str) -> bool:
        """Chunked download with progressive chunk sizes"""
        chunk_sizes = [1024*512, 1024*256, 1024*128, 1024*64]  # 512KB, 256KB, 128KB, 64KB
        
        for chunk_size in chunk_sizes:
            try:
                session = await self.get_session()
                async with session.get(download_url) as response:
                    if response.status == 200:
                        async with aiofiles.open(file_path, 'wb') as file:
                            async for chunk in response.content.iter_chunked(chunk_size):
                                await file.write(chunk)
                                await asyncio.sleep(0.01)  # Small delay to prevent overload
                        return True
            except Exception as e:
                logger.warning(f"Chunked download ({chunk_size} bytes) failed: {e}")
                continue
        return False
    
    async def _micro_download(self, download_url: str, file_path: str) -> bool:
        """Micro download - 1KB at a time, very slow but reliable"""
        try:
            session = await self.get_session()
            async with session.get(download_url) as response:
                if response.status == 200:
                    async with aiofiles.open(file_path, 'wb') as file:
                        while True:
                            chunk = await response.content.read(1024)  # 1KB
                            if not chunk:
                                break
                            await file.write(chunk)
                            await asyncio.sleep(0.05)  # Longer delay for stability
                    return True
        except Exception as e:
            logger.warning(f"Micro download failed: {e}")
        return False
    
    async def _resume_download(self, download_url: str, file_path: str) -> bool:
        """Resume download with range requests"""
        try:
            start_pos = 0
            if os.path.exists(file_path):
                start_pos = os.path.getsize(file_path)
            
            headers = {}
            if start_pos > 0:
                headers['Range'] = f'bytes={start_pos}-'
            
            session = await self.get_session()
            async with session.get(download_url, headers=headers) as response:
                if response.status in [200, 206]:  # 206 = Partial Content
                    mode = 'ab' if start_pos > 0 else 'wb'
                    async with aiofiles.open(file_path, mode) as file:
                        async for chunk in response.content.iter_chunked(8192):
                            await file.write(chunk)
                            await asyncio.sleep(0.02)
                    return True
        except Exception as e:
            logger.warning(f"Resume download failed: {e}")
        return False
    
    async def _patient_download(self, download_url: str, file_path: str) -> bool:
        """Most patient download method - maximum stability"""
        try:
            # Create new session with maximum patience
            timeout = aiohttp.ClientTimeout(
                total=600,      # 10 minutes total
                connect=60,     # 1 minute to connect  
                sock_read=120   # 2 minutes between reads
            )
            
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(download_url) as response:
                    if response.status == 200:
                        async with aiofiles.open(file_path, 'wb') as file:
                            bytes_downloaded = 0
                            async for chunk in response.content.iter_chunked(4096):  # 4KB chunks
                                await file.write(chunk)
                                bytes_downloaded += len(chunk)
                                
                                # Log progress every 1MB
                                if bytes_downloaded % (1024*1024) == 0:
                                    mb_downloaded = bytes_downloaded / (1024*1024)
                                    logger.info(f"📥 Downloaded: {mb_downloaded:.1f} MB")
                                
                                await asyncio.sleep(0.1)  # Very patient - 100ms delay
                        return True
        except Exception as e:
            logger.warning(f"Patient download failed: {e}")
        return False

# Create global instance
downloader = TeraboxDownloader()
                
