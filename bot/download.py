"""
Download functionality - Working WDZone API Implementation
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
            connector = aiohttp.TCPConnector(
                limit=50,
                limit_per_host=3,
                ttl_dns_cache=300,
                use_dns_cache=True,
                keepalive_timeout=60,
                enable_cleanup_closed=True
            )
            
            timeout = aiohttp.ClientTimeout(total=300)  # 5 minutes
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36'
                }
            )
        
        return self.session
    
    async def get_download_info(self, url: str, status_msg):
        """Get download URL and file info from WDZone API"""
        try:
            # Primary working API
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
                        f"📡 Using {api_config['type']} API\n"
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
        """Try API request with correct format"""
        try:
            session = await self.get_session()
            api_url = api_config['url']
            api_type = api_config['type']
            
            logger.info(f"🔍 Trying {api_type} API: {api_url}")
            
            if api_type == 'wdzone':
                # WDZone API - GET request with url parameter
                params = {'url': terabox_url}
                
                logger.info(f"📤 Making request to: {api_url} with params: {params}")
                
                async with session.get(api_url, params=params) as response:
                    logger.info(f"📥 Response status: {response.status}")
                    
                    if response.status == 200:
                        try:
                            result = await response.json()
                            logger.info(f"📋 WDZone API response keys: {list(result.keys())}")
                            
                            # Log first few chars of each value to debug
                            for k, v in result.items():
                                if isinstance(v, str):
                                    logger.info(f"   {k}: {v[:100]}...")
                                else:
                                    logger.info(f"   {k}: {type(v)} - {v}")
                            
                            # Parse WDZone API response format
                            # Look for status field (could have emoji)
                            status_field = None
                            info_field = None
                            
                            for key in result.keys():
                                if 'status' in key.lower():
                                    status_field = key
                                    logger.info(f"Found status field: {key}")
                                if 'info' in key.lower():
                                    info_field = key
                                    logger.info(f"Found info field: {key}")
                            
                            # Check if successful
                            if status_field and result.get(status_field) == 'Success':
                                logger.info("✅ API returned Success status")
                                
                                if info_field and result.get(info_field):
                                    extracted_info = result.get(info_field)
                                    logger.info(f"📊 Extracted info type: {type(extracted_info)}")
                                    
                                    if isinstance(extracted_info, list) and len(extracted_info) > 0:
                                        info = extracted_info[0]  # First file
                                        logger.info(f"📁 File info keys: {list(info.keys())}")
                                        
                                        # Extract download information
                                        download_url = None
                                        title = 'download'
                                        size = 'Unknown'
                                        
                                        # Find download URL field
                                        for key in info.keys():
                                            value = info.get(key)
                                            if isinstance(value, str):
                                                logger.info(f"   {key}: {value[:50]}...")
                                                
                                                if 'download' in key.lower() and ('http' in value or 'https' in value):
                                                    download_url = value
                                                    logger.info(f"🔗 Found download URL in field: {key}")
                                                
                                                if 'title' in key.lower() or 'name' in key.lower():
                                                    title = value
                                                    logger.info(f"📄 Found title in field: {key}")
                                                
                                                if 'size' in key.lower():
                                                    size = value
                                                    logger.info(f"📏 Found size in field: {key}")
                                        
                                        if download_url:
                                            logger.info(f"✅ Successfully extracted: {title} ({size})")
                                            return {
                                                'success': True,
                                                'download_url': download_url,
                                                'filename': title,
                                                'size': size
                                            }
                                        else:
                                            logger.warning("❌ No download URL found in file info")
                                    else:
                                        logger.warning(f"❌ Invalid extracted info format: {type(extracted_info)}")
                                else:
                                    logger.warning(f"❌ No info field found or empty")
                            else:
                                logger.warning(f"❌ API status not Success: {result.get(status_field) if status_field else 'No status field'}")
                        
                        except Exception as json_error:
                            logger.error(f"❌ JSON parsing error: {json_error}")
                            # Try to get response text for debugging
                            try:
                                text_response = await response.text()
                                logger.info(f"📄 Response text (first 500 chars): {text_response[:500]}")
                            except:
                                pass
                    else:
                        logger.error(f"❌ HTTP error: {response.status}")
            
            elif api_type == 'qtcloud':
                # QTCloud API - alternative format
                params = {'url': terabox_url}
                async with session.get(api_url, params=params) as response:
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"QTCloud response: {result}")
                        
                        if result.get('download_url'):
                            return {
                                'success': True,
                                'download_url': result['download_url'],
                                'filename': result.get('filename', 'download'),
                                'size': result.get('size', 'Unknown')
                            }
            
            logger.warning(f"❌ No valid response from {api_type}")
            return {'success': False, 'error': f'No download URL from {api_type}'}
            
        except asyncio.TimeoutError:
            logger.error(f"⏰ {api_type} API timeout")
            return {'success': False, 'error': f'{api_type} API timeout'}
        except Exception as e:
            logger.error(f"💥 API {api_type} error: {e}")
            return {'success': False, 'error': f'{api_type} API error: {str(e)}'}
    
    async def download_file(self, download_url: str, filename: str, status_msg):
        """Download file with progress"""
        try:
            filename = self._sanitize_filename(filename)
            file_path = os.path.join(config.DOWNLOAD_DIR, filename)
            os.makedirs(config.DOWNLOAD_DIR, exist_ok=True)
            
            logger.info(f"📥 Starting download: {file_path}")
            
            session = await self.get_session()
            
            async with session.get(download_url) as response:
                if response.status == 200:
                    total_size = int(response.headers.get('content-length', 0))
                    downloaded = 0
                    last_update = 0
                    
                    async with aiofiles.open(file_path, 'wb') as file:
                        async for chunk in response.content.iter_chunked(8192):
                            await file.write(chunk)
                            downloaded += len(chunk)
                            
                            # Update progress every 1MB
                            if downloaded - last_update >= 1024*1024 or downloaded >= total_size:
                                last_update = downloaded
                                if total_size > 0:
                                    progress = (downloaded / total_size) * 100
                                    try:
                                        await status_msg.edit_text(
                                            f"📥 **Downloading...**\n\n"
                                            f"📊 **Progress:** {progress:.1f}%\n"
                                            f"💾 **Downloaded:** {self._format_bytes(downloaded)}\n"
                                            f"📦 **Total:** {self._format_bytes(total_size)}",
                                            parse_mode='Markdown'
                                        )
                                    except:
                                        pass
                    
                    logger.info(f"✅ Download completed: {file_path}")
                    return file_path
                else:
                    logger.error(f"❌ Download failed: HTTP {response.status}")
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
                logger.info(f"🧹 Cleaned up: {file_path}")
        except Exception as e:
            logger.error(f"Cleanup error: {e}")
    
    async def close(self):
        """Close session"""
        if self.session:
            await self.session.close()
            
