"""
Download functionality - High-Speed Optimized Version
"""
import aiohttp
import asyncio
import aiofiles
import os
from loguru import logger
import config

class TeraboxDownloader:
    def __init__(self):
        # Connection pooling for better performance
        self.connector = None
        self.session = None
    
    async def get_session(self):
        """Get optimized HTTP session"""
        if not self.session or self.session.closed:
            # Optimized connector settings
            self.connector = aiohttp.TCPConnector(
                limit=100,              # Max connections
                limit_per_host=10,      # Max per host
                ttl_dns_cache=300,      # DNS cache
                use_dns_cache=True,
                keepalive_timeout=30,   # Keep connections alive
                enable_cleanup_closed=True
            )
            
            # Optimized timeout settings
            timeout = aiohttp.ClientTimeout(
                total=1800,      # 30 minutes total
                connect=30,      # 30 seconds to connect
                sock_read=300    # 5 minutes for reading chunks
            )
            
            self.session = aiohttp.ClientSession(
                connector=self.connector,
                timeout=timeout,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
            )
        
        return self.session
    
    async def get_download_info(self, url: str, status_msg):
        """Get download URL and file info from API - Optimized"""
        try:
            # Parallel API calls for faster response
            api_endpoints = [
                {
                    'url': 'https://wdzone-terabox-api.vercel.app/api',
                    'type': 'wdzone'
                },
                {
                    'url': 'https://terabox-dl.qtcloud.workers.dev/',
                    'type': 'qtcloud'
                },
                {
                    'url': 'https://api.teraboxapp.com/api/get-info',
                    'type': 'teraboxapp'
                }
            ]
            
            # Try APIs in parallel for speed
            tasks = []
            for i, api_config in enumerate(api_endpoints):
                task = asyncio.create_task(
                    self._try_api_request_fast(api_config, url)
                )
                tasks.append(task)
            
            await status_msg.edit_text(
                f"📡 **Getting download info...**\n\n"
                f"🚀 Trying {len(api_endpoints)} APIs simultaneously\n"
                f"⚡ Optimized for maximum speed...",
                parse_mode='Markdown'
            )
            
            # Wait for first successful response
            for completed_task in asyncio.as_completed(tasks):
                try:
                    result = await completed_task
                    if result['success']:
                        # Cancel remaining tasks
                        for task in tasks:
                            if not task.done():
                                task.cancel()
                        logger.info(f"✅ Fast API response received")
                        return result
                except:
                    continue
            
            return {'success': False, 'error': 'All APIs failed'}
            
        except Exception as e:
            return {'success': False, 'error': f'System error: {str(e)}'}
    
    async def _try_api_request_fast(self, api_config: dict, terabox_url: str):
        """Fast API request with optimizations"""
        try:
            session = await self.get_session()
            api_url = api_config['url']
            api_type = api_config['type']
            
            if api_type == 'wdzone':
                params = {'url': terabox_url}
                async with session.get(api_url, params=params) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        # Fast field detection
                        status_field = next((k for k in result.keys() if 'status' in k.lower()), None)
                        info_field = next((k for k in result.keys() if 'info' in k.lower()), None)
                        
                        if status_field and info_field and result.get(status_field) == 'Success':
                            extracted_info = result.get(info_field)
                            if isinstance(extracted_info, list) and len(extracted_info) > 0:
                                info = extracted_info[0]
                                
                                # Fast field extraction
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
        """High-speed file download with optimizations"""
        try:
            # Sanitize filename
            filename = self._sanitize_filename(filename)
            file_path = os.path.join(config.DOWNLOAD_DIR, filename)
            
            # Ensure download directory exists
            os.makedirs(config.DOWNLOAD_DIR, exist_ok=True)
            
            logger.info(f"📥 Starting high-speed download: {file_path}")
            
            session = await self.get_session()
            
            async with session.get(download_url) as response:
                if response.status == 200:
                    total_size = int(response.headers.get('content-length', 0))
                    downloaded = 0
                    last_update = 0
                    start_time = asyncio.get_event_loop().time()
                    
                    # High-speed chunk processing
                    async with aiofiles.open(file_path, 'wb') as file:
                        # Larger chunks for better speed (64KB instead of 8KB)
                        async for chunk in response.content.iter_chunked(65536):
                            await file.write(chunk)
                            downloaded += len(chunk)
                            
                            # Update progress every 10MB for better performance
                            if downloaded - last_update >= 10*1024*1024 or downloaded >= total_size:
                                last_update = downloaded
                                current_time = asyncio.get_event_loop().time()
                                elapsed = current_time - start_time
                                
                                if total_size > 0 and elapsed > 0:
                                    progress = (downloaded / total_size) * 100
                                    speed = downloaded / elapsed  # bytes per second
                                    speed_mb = speed / (1024 * 1024)  # MB/s
                                    
                                    eta = (total_size - downloaded) / speed if speed > 0 else 0
                                    eta_min = eta / 60
                                    
                                    try:
                                        await status_msg.edit_text(
                                            f"📥 **High-Speed Download**\n\n"
                                            f"📊 **Progress:** {progress:.1f}%\n"
                                            f"💾 **Downloaded:** {self._format_bytes(downloaded)}\n"
                                            f"📦 **Total:** {self._format_bytes(total_size)}\n"
                                            f"🚀 **Speed:** {speed_mb:.2f} MB/s\n"
                                            f"⏱️ **ETA:** {eta_min:.1f} minutes\n\n"
                                            f"⚡ **Optimized for maximum speed!**",
                                            parse_mode='Markdown'
                                        )
                                    except:
                                        pass  # Ignore message edit errors
                    
                    logger.info(f"✅ High-speed download completed: {file_path}")
                    return file_path
                else:
                    logger.error(f"❌ Download failed: HTTP {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"High-speed download error: {e}")
            return None
    
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
        """Close session and connector"""
        if self.session:
            await self.session.close()
        if self.connector:
            await self.connector.close()
            
