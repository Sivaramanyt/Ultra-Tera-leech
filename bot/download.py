"""
Download functionality for Terabox files
"""
import aiohttp
import asyncio
import aiofiles
import os
from loguru import logger
import config

class TeraboxDownloader:
    def __init__(self):
        pass
    
    async def get_download_info(self, url: str, status_msg):
        """Get download URL and file info from API"""
        try:
            # API endpoints
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
            
            for i, api_config in enumerate(api_endpoints):
                try:
                    await status_msg.edit_text(
                        f"📡 Getting download info...\n\n"
                        f"🔄 Server {i+1}/{len(api_endpoints)}\n"
                        f"⚡ Please wait..."
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
        """Try API to get download info"""
        try:
            timeout = aiohttp.ClientTimeout(total=30)
            async with aiohttp.ClientSession(timeout=timeout) as session:
                
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
                            
                            if status_field and info_field and result.get(status_field) == 'Success':
                                extracted_info = result.get(info_field)
                                if isinstance(extracted_info, list) and len(extracted_info) > 0:
                                    info = extracted_info[0]
                                    
                                    # Extract download info
                                    download_url = None
                                    title = 'download'
                                    size = 'Unknown'
                                    
                                    for key in info.keys():
                                        if 'download' in key.lower():
                                            download_url = info.get(key)
                                        if 'title' in key.lower() or 'name' in key.lower():
                                            title = info.get(key, 'download')
                                        if 'size' in key.lower():
                                            size = info.get(key, 'Unknown')
                                    
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
                            
                            if result.get('download'):
                                return {
                                    'success': True,
                                    'download_url': result['download'],
                                    'filename': result.get('name', 'download'),
                                    'size': result.get('size', 'Unknown')
                                }
            
            return {'success': False, 'error': 'No download URL found'}
            
        except Exception as e:
            return {'success': False, 'error': f'API error: {str(e)}'}
    
    async def download_file(self, download_url: str, filename: str, status_msg):
        """Download the actual file from direct URL"""
        try:
            # Sanitize filename
            filename = self._sanitize_filename(filename)
            file_path = os.path.join(config.DOWNLOAD_DIR, filename)
            
            # Make sure download directory exists
            os.makedirs(config.DOWNLOAD_DIR, exist_ok=True)
            
            logger.info(f"📥 Downloading file to: {file_path}")
            
            # Increased timeout for large files
            timeout = aiohttp.ClientTimeout(total=900)  # 15 minutes
            async with aiohttp.ClientSession(timeout=timeout) as session:
                async with session.get(download_url) as response:
                    if response.status == 200:
                        total_size = int(response.headers.get('content-length', 0))
                        downloaded = 0
                        last_update = 0
                        
                        async with aiofiles.open(file_path, 'wb') as file:
                            async for chunk in response.content.iter_chunked(8192):
                                await file.write(chunk)
                                downloaded += len(chunk)
                                
                                # Update progress every 5MB or at completion
                                if downloaded - last_update >= 5*1024*1024 or downloaded >= total_size:
                                    last_update = downloaded
                                    if total_size > 0:
                                        progress = (downloaded / total_size) * 100
                                        try:
                                            await status_msg.edit_text(
                                                f"📥 Downloading file...\n\n"
                                                f"📊 Progress: {progress:.1f}%\n"
                                                f"💾 Downloaded: {self._format_bytes(downloaded)}\n"
                                                f"📦 Total: {self._format_bytes(total_size)}\n"
                                                f"⏱️ Large files may take time..."
                                            )
                                        except:
                                            # Ignore message edit errors
                                            pass
                        
                        logger.info(f"✅ File downloaded successfully: {file_path}")
                        return file_path
                    else:
                        logger.error(f"❌ Download failed: HTTP {response.status}")
                        return None
                        
        except asyncio.TimeoutError:
            logger.error("❌ Download timeout - file too large or slow server")
            await status_msg.edit_text(
                "⏰ Download Timeout\n\n"
                "The file is taking too long to download.\n"
                "This might be due to:\n"
                "• Large file size\n" 
                "• Slow Terabox servers\n"
                "• Network issues\n\n"
                "Please try again later!"
            )
            return None
        except Exception as e:
            logger.error(f"Download error: {e}")
            return None
    
    def _sanitize_filename(self, filename: str) -> str:
        """Clean filename for safe storage"""
        import re
        # Remove invalid characters
        filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Limit length
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
