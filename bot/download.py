"""
Download functionality - Enhanced with Retry Mechanism
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
        """Get HTTP session"""
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
        """Get download URL from WDZone API"""
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
                            filename = 'download'
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
        """Enhanced download with speed optimization and retry mechanism"""
        try:
            filename = self._sanitize_filename(filename)
            file_path = os.path.join(config.DOWNLOAD_DIR, filename)
            os.makedirs(config.DOWNLOAD_DIR, exist_ok=True)
            
            # Remove old file
            if os.path.exists(file_path):
                os.remove(file_path)
            
            session = await self.get_session()
            
            async with session.get(download_url) as response:
                if response.status == 200:
                    total_size = int(response.headers.get('content-length', 0))
                    downloaded = 0
                    last_update = 0
                    start_time = asyncio.get_event_loop().time()
                    
                    async with aiofiles.open(file_path, 'wb') as file:
                        try:
                            # First attempt: Large chunks for speed (512KB)
                            async for chunk in response.content.iter_chunked(524288):  # 512KB chunks
                                await file.write(chunk)
                                downloaded += len(chunk)
                                
                                # Update every 3MB for better speed
                                if downloaded - last_update >= 3145728 or downloaded >= total_size:
                                    last_update = downloaded
                                    elapsed = asyncio.get_event_loop().time() - start_time
                                    if total_size > 0 and elapsed > 0:
                                        progress = (downloaded / total_size) * 100
                                        speed = downloaded / elapsed / (1024 * 1024)  # MB/s
                                        try:
                                            await status_msg.edit_text(
                                                f"📥 High-Speed Download\n\n"
                                                f"Progress: {progress:.1f}%\n"
                                                f"Speed: {speed:.1f} MB/s\n"
                                                f"Downloaded: {self._format_bytes(downloaded)}\n"
                                                f"Total: {self._format_bytes(total_size)}",
                                                parse_mode=None
                                            )
                                        except:
                                            pass
                        
                        except Exception as chunk_error:
                            logger.warning(f"Large chunk download failed: {chunk_error}")
                            
                            # Retry with smaller chunks (64KB)
                            logger.info("🔄 Retrying with smaller chunks...")
                            await status_msg.edit_text("🔄 Retrying with smaller chunks...", parse_mode=None)
                            
                            # Reset file and position
                            await file.seek(0)
                            await file.truncate(0)
                            downloaded = 0
                            
                            # Second attempt: Smaller chunks for stability
                            async with session.get(download_url) as retry_response:
                                if retry_response.status == 200:
                                    async for chunk in retry_response.content.iter_chunked(65536):  # 64KB chunks
                                        await file.write(chunk)
                                        downloaded += len(chunk)
                                        
                                        # Update every 1MB for smaller chunks
                                        if downloaded % (1024*1024) == 0 or downloaded >= total_size:
                                            if total_size > 0:
                                                progress = (downloaded / total_size) * 100
                                                try:
                                                    await status_msg.edit_text(
                                                        f"📥 Stable Download (Retry)\n\n"
                                                        f"Progress: {progress:.1f}%\n"
                                                        f"Downloaded: {self._format_bytes(downloaded)}\n"
                                                        f"Total: {self._format_bytes(total_size)}\n"
                                                        f"Mode: 64KB chunks",
                                                        parse_mode=None
                                                    )
                                                except:
                                                    pass
                    
                    # Verify download completion
                    if os.path.exists(file_path):
                        final_size = os.path.getsize(file_path)
                        if final_size > 0:
                            logger.info(f"✅ Download completed: {final_size} bytes")
                            return file_path
                    
                    return None
                else:
                    logger.error(f"HTTP {response.status}")
                    return None
            
        except Exception as e:
            logger.error(f"Download error: {e}")
            
            # Final retry with micro chunks (8KB) for very unstable connections
            try:
                logger.info("🔄 Final retry with micro chunks...")
                await status_msg.edit_text("🔄 Final retry attempt...", parse_mode=None)
                
                session = await self.get_session()
                async with session.get(download_url) as final_response:
                    if final_response.status == 200:
                        async with aiofiles.open(file_path, 'wb') as file:
                            downloaded = 0
                            async for chunk in final_response.content.iter_chunked(8192):  # 8KB chunks
                                await file.write(chunk)
                                downloaded += len(chunk)
                        
                        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                            logger.info("✅ Final retry successful")
                            return file_path
                            
            except Exception as final_error:
                logger.error(f"Final retry failed: {final_error}")
            
            return None
    
    def _sanitize_filename(self, filename: str) -> str:
        """Clean filename"""
        import re
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        return filename[:200] if len(filename) > 200 else filename
    
    def _format_bytes(self, bytes_count: int) -> str:
        """Format bytes to human readable"""
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
                            
