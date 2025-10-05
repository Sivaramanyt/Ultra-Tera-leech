"""
Download functionality - Connection-Resilient Version (Fixed)
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
        """Get optimized HTTP session with resilient settings"""
        if not self.session or self.session.closed:
            connector = aiohttp.TCPConnector(
                limit=50,
                limit_per_host=3,    # Fixed: Only one limit_per_host
                ttl_dns_cache=300,
                use_dns_cache=True,
                keepalive_timeout=60,
                enable_cleanup_closed=True,
                force_close=True
            )
            
            timeout = aiohttp.ClientTimeout(
                total=1800,      # 30 minutes
                connect=30,      # 30 seconds to connect
                sock_read=120,   # 2 minutes for reading
                sock_connect=30  # 30 seconds socket connect
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
        """Get download URL and file info from API"""
        try:
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
            
            # Try APIs sequentially for stability
            for i, api_config in enumerate(api_endpoints):
                try:
                    await status_msg.edit_text(
                        f"📡 **Getting download info...**\n\n"
                        f"🔄 Server {i+1}/{len(api_endpoints)}\n"
                        f"⚡ Please wait...",
                        parse_mode='Markdown'
                    )
                    
                    result = await self._try_api_request(api_config, url)
                    
                    if result['success']:
                        logger.info(f"✅ Got download info from: {api_config['url']}")
                        return result
                        
                except Exception as e:
                    logger.warning(f"API {api_config['url']} failed: {e}")
                    continue
            
            return {'success': False, 'error': 'All APIs failed'}
            
        except Exception as e:
            return {'success': False, 'error': f'System error: {str(e)}'}
    
    async def _try_api_request(self, api_config: dict, terabox_url: str):
        """Try API request with error handling"""
        try:
            session = await self.get_session()
            api_url = api_config['url']
            api_type = api_config['type']
            
            if api_type == 'wdzone':
                params = {'url': terabox_url}
                async with session.get(api_url, params=params) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        # Find status and info fields
                        status_field = next((k for k in result.keys() if 'status' in k.lower()), None)
                        info_field = next((k for k in result.keys() if 'info' in k.lower()), None)
                        
                        if status_field and info_field and result.get(status_field) == 'Success':
                            extracted_info = result.get(info_field)
                            if isinstance(extracted_info, list) and len(extracted_info) > 0:
                                info = extracted_info[0]
                                
                                download_url = next((info.get(k) for k in info.keys() if 'download' in k.lower()), None)
                                title = next((info.get(k) for k in info.keys() if 'title' in k.lower() or 'name' in k.lower()), 'download')
                                size = next((info.get(k) for k in info.keys() if 'size' in k.lower()), 'Unknown')
                                
                                if download_url:
                                    return {
                                        'success': True,
                                        'download_url': download_url,
                                        'filename': title,
                                        'size': size
                                    }
            
            return {'success': False, 'error': 'No download URL found'}
            
        except Exception as e:
            return {'success': False, 'error': f'API error: {str(e)}'}
    
    async def download_file(self, download_url: str, filename: str, status_msg):
        """Resilient file download with retry logic"""
        try:
            filename = self._sanitize_filename(filename)
            file_path = os.path.join(config.DOWNLOAD_DIR, filename)
            os.makedirs(config.DOWNLOAD_DIR, exist_ok=True)
            
            logger.info(f"📥 Starting resilient download: {file_path}")
            
            # Retry logic for connection drops
            max_retries = 3
            retry_delay = 5
            
            for attempt in range(max_retries):
                try:
                    if attempt > 0:
                        await status_msg.edit_text(
                            f"🔄 **Download Retry {attempt + 1}/{max_retries}**\n\n"
                            f"📁 **File:** {filename[:40]}...\n"
                            f"⏳ Reconnecting to server...",
                            parse_mode='Markdown'
                        )
                        await asyncio.sleep(retry_delay)
                    
                    # Try to download
                    result = await self._download_with_resume(download_url, file_path, status_msg, attempt)
                    
                    if result:
                        logger.info(f"✅ Download completed: {file_path}")
                        return file_path
                        
                except Exception as e:
                    logger.warning(f"Download attempt {attempt + 1} failed: {e}")
                    if attempt < max_retries - 1:
                        continue
                    else:
                        raise
            
            return None
                        
        except Exception as e:
            logger.error(f"Download error: {e}")
            await status_msg.edit_text(
                "❌ **Download Failed**\n\n"
                "Connection issues prevented download.\n"
                "This could be due to:\n"
                "• Large file size\n"
                "• Server instability\n"
                "• Network timeout\n\n"
                "Please try again later!",
                parse_mode='Markdown'
            )
            return None
    
    async def _download_with_resume(self, download_url: str, file_path: str, status_msg, attempt: int):
        """Download with resume capability"""
        try:
            session = await self.get_session()
            
            # Check if partial file exists
            resume_pos = 0
            if os.path.exists(file_path) and attempt > 0:
                resume_pos = os.path.getsize(file_path)
                logger.info(f"📄 Resuming from position: {resume_pos}")
            
            # Set resume header if needed
            headers = {}
            if resume_pos > 0:
                headers['Range'] = f'bytes={resume_pos}-'
            
            async with session.get(download_url, headers=headers) as response:
                if response.status in [200, 206]:  # 206 for partial content
                    total_size = resume_pos
                    if 'content-range' in response.headers:
                        # Parse content-range header
                        content_range = response.headers['content-range']
                        total_size = int(content_range.split('/')[-1])
                    elif 'content-length' in response.headers:
                        total_size = int(response.headers['content-length']) + resume_pos
                    
                    downloaded = resume_pos
                    last_update = 0
                    start_time = asyncio.get_event_loop().time()
                    
                    # Open file in append mode if resuming, write mode if new
                    mode = 'ab' if resume_pos > 0 else 'wb'
                    
                    async with aiofiles.open(file_path, mode) as file:
                        # Smaller chunks for stability (32KB)
                        chunk_size = 32768
                        
                        try:
                            async for chunk in response.content.iter_chunked(chunk_size):
                                await file.write(chunk)
                                downloaded += len(chunk)
                                
                                # Update progress every 5MB
                                if downloaded - last_update >= 5*1024*1024 or downloaded >= total_size:
                                    last_update = downloaded
                                    current_time = asyncio.get_event_loop().time()
                                    elapsed = current_time - start_time
                                    
                                    if total_size > 0 and elapsed > 0:
                                        progress = (downloaded / total_size) * 100
                                        speed = (downloaded - resume_pos) / elapsed if elapsed > 0 else 0
                                        speed_mb = speed / (1024 * 1024)
                                        
                                        try:
                                            await status_msg.edit_text(
                                                f"📥 **Stable Download**\n\n"
                                                f"📊 **Progress:** {progress:.1f}%\n"
                                                f"💾 **Downloaded:** {self._format_bytes(downloaded)}\n"
                                                f"📦 **Total:** {self._format_bytes(total_size)}\n"
                                                f"🚀 **Speed:** {speed_mb:.1f} MB/s\n"
                                                f"🔄 **Attempt:** {attempt + 1}\n\n"
                                                f"⚡ **Optimized for stability!**",
                                                parse_mode='Markdown'
                                            )
                                        except:
                                            pass
                        
                        except asyncio.IncompleteReadError:
                            logger.warning("Incomplete read - checking if download is complete")
                            # Check if we got most of the file (95% or more)
                            if total_size > 0 and downloaded >= total_size * 0.95:
                                logger.info(f"Download 95%+ complete ({downloaded}/{total_size})")
                                return True
                            return False
                    
                    return True
                else:
                    logger.error(f"❌ Download failed: HTTP {response.status}")
                    return False
                    
        except Exception as e:
            logger.error(f"Download chunk error: {e}")
            return False
    
    def _sanitize_filename(self, filename: str) -> str:
        """Clean filename for safe storage"""
        import re
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
        """Clean up downloaded file"""
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
                        
