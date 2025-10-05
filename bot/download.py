"""
Download functionality - Clean Optimized Version
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
        """Get optimized HTTP session"""
        if not self.session or self.session.closed:
            connector = aiohttp.TCPConnector(
                limit=100,
                limit_per_host=10,
                ttl_dns_cache=300,
                use_dns_cache=True,
                keepalive_timeout=90,
                enable_cleanup_closed=True
            )
            
            timeout = aiohttp.ClientTimeout(total=900)  # 15 minutes
            
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
                    'url': 'https://teraboxdl.qtcloud.workers.dev/api',  
                    'type': 'qtcloud'
                }
            ]
            
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
                        return result
                        
                except Exception as e:
                    continue
            
            return {'success': False, 'error': 'All APIs failed'}
            
        except Exception as e:
            return {'success': False, 'error': f'System error: {str(e)}'}
    
    async def _try_api_request(self, api_config: dict, terabox_url: str):
        """Try API request with correct format"""
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
                        status_field = None
                        info_field = None
                        
                        for key in result.keys():
                            if 'status' in key.lower():
                                status_field = key
                            if 'info' in key.lower():
                                info_field = key
                        
                        # Check if successful
                        if status_field and result.get(status_field) == 'Success':
                            if info_field and result.get(info_field):
                                extracted_info = result.get(info_field)
                                
                                if isinstance(extracted_info, list) and len(extracted_info) > 0:
                                    info = extracted_info[0]
                                    
                                    # Extract download information
                                    download_url = None
                                    title = 'download'
                                    size = 'Unknown'
                                    
                                    for key in info.keys():
                                        value = info.get(key)
                                        if isinstance(value, str):
                                            if 'download' in key.lower() and ('http' in value or 'https' in value):
                                                download_url = value
                                            
                                            if 'title' in key.lower() or 'name' in key.lower():
                                                title = value
                                            
                                            if 'size' in key.lower():
                                                size = value
                                    
                                    if download_url:
                                        return {
                                            'success': True,
                                            'download_url': download_url,
                                            'filename': title,
                                            'size': size
                                        }
                        
            elif api_type == 'qtcloud':
                params = {'url': terabox_url}
                async with session.get(api_url, params=params) as response:
                    if response.status == 200:
                        result = await response.json()
                        
                        if result.get('download_url'):
                            return {
                                'success': True,
                                'download_url': result['download_url'],
                                'filename': result.get('filename', 'download'),
                                'size': result.get('size', 'Unknown')
                            }
            
            return {'success': False, 'error': f'No download URL from {api_type}'}
            
        except Exception as e:
            return {'success': False, 'error': f'{api_type} API error: {str(e)}'}
    
    async def download_file(self, download_url: str, filename: str, status_msg):
        """High-speed optimized download"""
        try:
            filename = self._sanitize_filename(filename)
            file_path = os.path.join(config.DOWNLOAD_DIR, filename)
            os.makedirs(config.DOWNLOAD_DIR, exist_ok=True)
            
            session = await self.get_session()
            
            async with session.get(download_url) as response:
                if response.status == 200:
                    total_size = int(response.headers.get('content-length', 0))
                    downloaded = 0
                    last_update = 0
                    start_time = asyncio.get_event_loop().time()
                    
                    # Large chunks for maximum speed
                    chunk_size = 512 * 1024  # 512KB chunks
                    
                    async with aiofiles.open(file_path, 'wb') as file:
                        async for chunk in response.content.iter_chunked(chunk_size):
                            await file.write(chunk)
                            downloaded += len(chunk)
                            
                            # Update progress every 5MB for better performance
                            if downloaded - last_update >= 5*1024*1024 or downloaded >= total_size:
                                last_update = downloaded
                                current_time = asyncio.get_event_loop().time()
                                elapsed = current_time - start_time
                                
                                if total_size > 0 and elapsed > 0:
                                    progress = (downloaded / total_size) * 100
                                    speed = downloaded / elapsed
                                    speed_mb = speed / (1024 * 1024)
                                    
                                    try:
                                        await status_msg.edit_text(
                                            f"🚀 **High-Speed Download**\n\n"
                                            f"📊 **Progress:** {progress:.1f}%\n"
                                            f"💾 **Downloaded:** {self._format_bytes(downloaded)}\n"
                                            f"📦 **Total:** {self._format_bytes(total_size)}\n"
                                            f"⚡ **Speed:** {speed_mb:.1f} MB/s",
                                            parse_mode='Markdown'
                                        )
                                    except:
                                        pass
                    
                    return file_path
                else:
                    return None
                    
        except Exception as e:
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
        except Exception as e:
            pass
    
    async def close(self):
        """Close session"""
        if self.session:
            await self.session.close()
                                        
