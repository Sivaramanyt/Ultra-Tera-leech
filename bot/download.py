"""
Download functionality - Multiple APIs + Ultra Stable
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
        """Try multiple APIs for better success rate"""
        apis = [
            {
                'name': 'WDZone',
                'url': 'https://wdzone-terabox-api.vercel.app/api',
                'params': {'url': url}
            },
            {
                'name': 'TeraboxDL',
                'url': 'https://teraboxdl.qtcloud.workers.dev/api', 
                'params': {'url': url}
            }
        ]
        
        for i, api in enumerate(apis):
            try:
                await status_msg.edit_text(
                    f"📡 Trying API {i+1}/{len(apis)}\n\n"
                    f"🔄 {api['name']} server...",
                    parse_mode=None
                )
                
                result = await self._try_single_api(api, url)
                if result['success']:
                    logger.info(f"✅ {api['name']} API Success - File: {result['filename']}, Size: {result['size']}")
                    return result
                    
            except Exception as e:
                logger.error(f"{api['name']} API failed: {e}")
                continue
        
        return {'success': False, 'error': 'All APIs failed'}
    
    async def _try_single_api(self, api_config: dict, terabox_url: str):
        """Try single API"""
        try:
            session = await self.get_session()
            
            async with session.get(api_config['url'], params=api_config['params']) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    # WDZone format
                    if api_config['name'] == 'WDZone':
                        status_field = next((k for k in result.keys() if 'status' in k.lower()), None)
                        info_field = next((k for k in result.keys() if 'info' in k.lower()), None)
                        
                        if status_field and info_field and result.get(status_field) == 'Success':
                            extracted_info = result.get(info_field)
                            if isinstance(extracted_info, list) and len(extracted_info) > 0:
                                info = extracted_info[0]
                                
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
                                    return {
                                        'success': True,
                                        'download_url': download_url,
                                        'filename': filename,
                                        'size': size
                                    }
                    
                    # TeraboxDL format  
                    elif api_config['name'] == 'TeraboxDL':
                        if result.get('download_url'):
                            return {
                                'success': True,
                                'download_url': result['download_url'],
                                'filename': result.get('filename', 'download'),
                                'size': result.get('size', 'Unknown')
                            }
            
            return {'success': False, 'error': f'{api_config["name"]} - No download URL'}
            
        except Exception as e:
            return {'success': False, 'error': f'{api_config["name"]} error: {str(e)}'}
    
    async def download_file(self, download_url: str, filename: str, status_msg):
        """Ultra-stable micro-chunk download with multiple retries"""
        try:
            filename = self._sanitize_filename(filename)
            file_path = os.path.join(config.DOWNLOAD_DIR, filename)
            os.makedirs(config.DOWNLOAD_DIR, exist_ok=True)
            
            # Multiple attempts with different chunk sizes
            chunk_sizes = [4096, 2048, 1024]  # 4KB, 2KB, 1KB
            max_retries = 3
            
            for attempt in range(max_retries):
                for chunk_size in chunk_sizes:
                    try:
                        await status_msg.edit_text(
                            f"📥 Download Attempt {attempt+1}/{max_retries}\n\n"
                            f"📁 File: {filename[:30]}...\n"
                            f"🔧 Chunk: {chunk_size//1024}KB\n"
                            f"⏳ Starting...",
                            parse_mode=None
                        )
                        
                        # Remove old file
                        if os.path.exists(file_path):
                            os.remove(file_path)
                        
                        # Micro timeout per attempt
                        connector = aiohttp.TCPConnector(limit=1, limit_per_host=1)
                        timeout = aiohttp.ClientTimeout(
                            total=300,    # 5 minutes total
                            connect=10,   # 10 seconds to connect
                            sock_read=30  # 30 seconds between chunks
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
                                    
                                    async with aiofiles.open(file_path, 'wb') as file:
                                        async for chunk in response.content.iter_chunked(chunk_size):
                                            await file.write(chunk)
                                            downloaded += len(chunk)
                                            
                                            # Update every 500KB
                                            if downloaded % (500*1024) < chunk_size or downloaded >= total_size:
                                                if total_size > 0:
                                                    progress = (downloaded / total_size) * 100
                                                    try:
                                                        await status_msg.edit_text(
                                                            f"📥 Micro-Download\n\n"
                                                            f"📊 Progress: {progress:.1f}%\n"
                                                            f"💾 Downloaded: {self._format_bytes(downloaded)}\n"
                                                            f"📦 Total: {self._format_bytes(total_size)}\n"
                                                            f"🔧 Chunk: {chunk_size//1024}KB\n"
                                                            f"🔄 Try: {attempt+1}",
                                                            parse_mode=None
                                                        )
                                                    except:
                                                        pass
                                    
                                    # Verify success
                                    if os.path.exists(file_path):
                                        final_size = os.path.getsize(file_path)
                                        if total_size == 0 or final_size >= total_size * 0.9:
                                            logger.info(f"✅ Download success with {chunk_size//1024}KB chunks: {final_size} bytes")
                                            return file_path
                        
                        # If we get here, try smaller chunks
                        continue
                        
                    except Exception as e:
                        logger.warning(f"Attempt {attempt+1} with {chunk_size//1024}KB failed: {e}")
                        continue
                
                # Wait before retry
                if attempt < max_retries - 1:
                    await asyncio.sleep(3)
            
            # All attempts failed
            await status_msg.edit_text(
                "❌ All Download Attempts Failed\n\n"
                "The Terabox servers are unstable.\n"
                "Please try:\n"
                "• Different Terabox link\n"
                "• Again in 10-15 minutes\n"
                "• Smaller file size",
                parse_mode=None
            )
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
        
