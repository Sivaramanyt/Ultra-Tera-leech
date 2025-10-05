"""
Download functionality - Safe Markdown Version
"""
import aiohttp
import asyncio
import aiofiles
import os
import re
from loguru import logger
import config

class TeraboxDownloader:
    def __init__(self):
        self.session = None
    
    async def get_session(self):
        """Get HTTP session"""
        if not self.session or self.session.closed:
            connector = aiohttp.TCPConnector(
                limit=50,
                limit_per_host=5,
                ttl_dns_cache=300,
                use_dns_cache=True,
                keepalive_timeout=60,
                enable_cleanup_closed=True
            )
            
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
            await status_msg.edit_text(
                "📡 Getting download info...\n\n⚡ Please wait...",
                parse_mode=None  # No Markdown
            )
            
            session = await self.get_session()
            api_url = 'https://wdzone-terabox-api.vercel.app/api'
            
            async with session.get(api_url, params={'url': url}) as response:
                if response.status == 200:
                    result = await response.json()
                    logger.info(f"API Response: {result}")
                    
                    # Look for Success status
                    if any('Success' in str(v) for v in result.values()):
                        # Find the info array
                        info_array = None
                        for value in result.values():
                            if isinstance(value, list) and len(value) > 0:
                                info_array = value
                                break
                        
                        if info_array:
                            file_info = info_array[0]
                            
                            # Extract data - look for download URL
                            download_url = None
                            filename = 'download'
                            size = 'Unknown'
                            
                            for key, value in file_info.items():
                                if isinstance(value, str):
                                    if 'download' in key.lower() and value.startswith('https://'):
                                        download_url = value
                                    elif 'title' in key.lower() or 'name' in key.lower():
                                        filename = value
                                    elif 'size' in key.lower():
                                        size = value
                            
                            if download_url:
                                logger.info(f"✅ Found: {filename} ({size}) - {download_url[:50]}...")
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
        """Safe download with no Markdown parsing errors"""
        try:
            filename = self._sanitize_filename(filename)
            file_path = os.path.join(config.DOWNLOAD_DIR, filename)
            os.makedirs(config.DOWNLOAD_DIR, exist_ok=True)
            
            # Remove old file
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # Clean filename for display (remove special characters that break Markdown)
            safe_filename = re.sub(r'[^\w\s.-]', '', filename)[:30]
            
            await status_msg.edit_text(
                f"🚀 Starting Download\n\n📁 File: {safe_filename}...",
                parse_mode=None  # No Markdown parsing
            )
            
            # Simple download session
            connector = aiohttp.TCPConnector(
                limit=1,
                limit_per_host=1,
                keepalive_timeout=300
            )
            
            timeout = aiohttp.ClientTimeout(total=1800)  # 30 minutes
            
            async with aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
            ) as session:
                
                async with session.get(download_url, allow_redirects=True) as response:
                    if response.status == 200:
                        total_size = int(response.headers.get('content-length', 0))
                        downloaded = 0
                        
                        # Large chunks for speed
                        chunk_size = 1024 * 1024  # 1MB chunks
                        
                        async with aiofiles.open(file_path, 'wb') as file:
                            async for chunk in response.content.iter_chunked(chunk_size):
                                await file.write(chunk)
                                downloaded += len(chunk)
                                
                                # Update every 5MB - NO MARKDOWN
                                if downloaded % (5 * 1024 * 1024) < chunk_size or downloaded >= total_size:
                                    if total_size > 0:
                                        progress = (downloaded / total_size) * 100
                                        try:
                                            await status_msg.edit_text(
                                                f"🚀 Downloading\n\n"
                                                f"📊 Progress: {progress:.1f}%\n"
                                                f"💾 Downloaded: {self._format_bytes(downloaded)}\n"
                                                f"📦 Total: {self._format_bytes(total_size)}",
                                                parse_mode=None  # No Markdown
                                            )
                                        except:
                                            pass
                        
                        # Check completion
                        if os.path.exists(file_path):
                            final_size = os.path.getsize(file_path)
                            if total_size == 0 or final_size >= total_size * 0.9:
                                logger.info(f"✅ Download success: {final_size} bytes")
                                return file_path
                        
                        await status_msg.edit_text(
                            "❌ Download incomplete\n\nPlease try again!",
                            parse_mode=None
                        )
                        return None
                    else:
                        await status_msg.edit_text(
                            f"❌ Server Error {response.status}\n\nPlease try again!",
                            parse_mode=None
                        )
                        return None
                        
        except Exception as e:
            logger.error(f"Download error: {e}")
            await status_msg.edit_text(
                "❌ Download failed\n\nPlease try again!",
                parse_mode=None
            )
            return None
    
    def _sanitize_filename(self, filename: str) -> str:
        """Clean filename for file system"""
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
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
            
