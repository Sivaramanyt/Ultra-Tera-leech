"""
Download functionality - WDZone Only Fast Version
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
        """Get optimized HTTP session for speed"""
        if not self.session or self.session.closed:
            connector = aiohttp.TCPConnector(
                limit=10,
                limit_per_host=5,
                ttl_dns_cache=300,
                use_dns_cache=True,
                keepalive_timeout=120,
                enable_cleanup_closed=True
            )
            
            timeout = aiohttp.ClientTimeout(total=600)  # 10 minutes
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
        return self.session
    
    async def get_download_info(self, url: str, status_msg):
        """WDZone API only - Fast extraction"""
        try:
            await status_msg.edit_text("📡 Getting download info...", parse_mode=None)
            
            session = await self.get_session()
            api_url = 'https://wdzone-terabox-api.vercel.app/api'
            
            async with session.get(api_url, params={'url': url}) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    # WDZone format - find status and info fields
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
            logger.error(f"WDZone API Error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def download_file(self, download_url: str, filename: str, status_msg):
        """Fast optimized download - Large chunks for speed"""
        try:
            filename = self._sanitize_filename(filename)
            file_path = os.path.join(config.DOWNLOAD_DIR, filename)
            os.makedirs(config.DOWNLOAD_DIR, exist_ok=True)
            
            # Remove old file
            if os.path.exists(file_path):
                os.remove(file_path)
            
            await status_msg.edit_text("📥 Starting fast download...", parse_mode=None)
            
            # Fast download session with optimized settings
            connector = aiohttp.TCPConnector(
                limit=3,
                limit_per_host=3,
                keepalive_timeout=300,  # 5 minutes
                enable_cleanup_closed=True
            )
            
            timeout = aiohttp.ClientTimeout(
                total=1800,    # 30 minutes
                connect=30,    # 30 seconds to connect
                sock_read=120  # 2 minutes between chunks
            )
            
            async with aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            ) as session:
                
                async with session.get(download_url, allow_redirects=True) as response:
                    if response.status == 200:
                        total_size = int(response.headers.get('content-length', 0))
                        downloaded = 0
                        last_update = 0
                        start_time = asyncio.get_event_loop().time()
                        
                        # Large chunks for maximum speed
                        chunk_size = 512 * 1024  # 512KB chunks for speed
                        
                        async with aiofiles.open(file_path, 'wb') as file:
                            async for chunk in response.content.iter_chunked(chunk_size):
                                await file.write(chunk)
                                downloaded += len(chunk)
                                
                                # Update every 2MB for better speed
                                if downloaded - last_update >= 2*1024*1024 or downloaded >= total_size:
                                    last_update = downloaded
                                    current_time = asyncio.get_event_loop().time()
                                    elapsed = current_time - start_time
                                    
                                    if total_size > 0 and elapsed > 0:
                                        progress = (downloaded / total_size) * 100
                                        speed = downloaded / elapsed
                                        speed_mb = speed / (1024 * 1024)
                                        eta = (total_size - downloaded) / speed if speed > 0 else 0
                                        eta_min = eta / 60
                                        
                                        try:
                                            await status_msg.edit_text(
                                                f"📥 Fast Download\n\n"
                                                f"📊 Progress: {progress:.1f}%\n"
                                                f"💾 Downloaded: {self._format_bytes(downloaded)}\n"
                                                f"📦 Total: {self._format_bytes(total_size)}\n"
                                                f"⚡ Speed: {speed_mb:.1f} MB/s\n"
                                                f"⏱️ ETA: {eta_min:.1f} min\n"
                                                f"🔧 512KB chunks",
                                                parse_mode=None
                                            )
                                        except:
                                            pass
                        
                        # Verify download
                        if os.path.exists(file_path):
                            final_size = os.path.getsize(file_path)
                            if total_size == 0 or final_size >= total_size * 0.95:
                                logger.info(f"✅ Fast download completed: {final_size} bytes")
                                return file_path
                        
                        await status_msg.edit_text(
                            "❌ Download incomplete\n\nFile may be corrupted. Try again!",
                            parse_mode=None
                        )
                        return None
                    else:
                        await status_msg.edit_text(
                            f"❌ Server Error {response.status}\n\nTry again later!",
                            parse_mode=None
                        )
                        return None
                        
        except asyncio.TimeoutError:
            await status_msg.edit_text(
                "❌ Download Timeout\n\nTerabox servers are slow today.\nTry again in 10-15 minutes!",
                parse_mode=None
            )
            return None
            
        except Exception as e:
            logger.error(f"Download error: {e}")
            await status_msg.edit_text(
                "❌ Download Failed\n\nTerabox servers are unstable.\nPlease try again later!",
                parse_mode=None
            )
            return None
    
    def _sanitize_filename(self, filename: str) -> str:
        """Clean filename"""
        import re
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        if len(filename) > 200:
            name, ext = filename.rsplit('.', 1) if '.' in filename else (filename, '')
            filename = name[:200-len(ext)-1] + '.' + ext if ext else name[:200]
        return filename
    
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
        except Exception as e:
            pass
    
    async def close(self):
        """Close session"""
        if self.session:
            await self.session.close()
                                    
