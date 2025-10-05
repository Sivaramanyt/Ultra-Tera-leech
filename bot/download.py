"""
Download functionality - Resume-Capable Ultimate Version
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
                        logger.info(f"✅ API Success: {result['filename']} ({result['size']})")
                        return result
                        
                except Exception as e:
                    logger.error(f"API {api_config['type']} error: {e}")
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
                params = {'url': terabox_url}
                
                async with session.get(api_url, params=params) as response:
                    logger.info(f"📥 API Response status: {response.status}")
                    
                    if response.status == 200:
                        result = await response.json()
                        logger.info(f"📋 API response keys: {list(result.keys())}")
                        
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
                                                logger.info(f"🔗 Found download URL: {download_url[:50]}...")
                                            
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
                                    else:
                                        logger.error("❌ No download URL found in API response")
                        else:
                            logger.error(f"❌ API returned non-success status: {result.get(status_field)}")
                    else:
                        logger.error(f"❌ API HTTP error: {response.status}")
                        
            elif api_type == 'qtcloud':
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
            
            return {'success': False, 'error': f'No download URL from {api_type}'}
            
        except Exception as e:
            logger.error(f"💥 API {api_type} exception: {e}")
            return {'success': False, 'error': f'{api_type} API error: {str(e)}'}
    
    async def download_file(self, download_url: str, filename: str, status_msg):
        """Resume-capable download with aggressive connection handling"""
        try:
            filename = self._sanitize_filename(filename)
            file_path = os.path.join(config.DOWNLOAD_DIR, filename)
            os.makedirs(config.DOWNLOAD_DIR, exist_ok=True)
            
            logger.info(f"🚀 Starting resume-capable download: {filename}")
            
            max_retries = 5  # More retries
            retry_delay = 1  # Faster retry
            total_downloaded = 0
            
            for attempt in range(max_retries):
                try:
                    # Check if partial file exists
                    if os.path.exists(file_path):
                        total_downloaded = os.path.getsize(file_path)
                        logger.info(f"📄 Resuming from {self._format_bytes(total_downloaded)}")
                    else:
                        total_downloaded = 0
                    
                    if attempt > 0:
                        await status_msg.edit_text(
                            f"🔄 **Resume Attempt {attempt + 1}/{max_retries}**\n\n"
                            f"📁 **File:** {filename[:25]}...\n"
                            f"📊 **Resumed:** {self._format_bytes(total_downloaded)}\n"
                            f"⏳ Reconnecting...",
                            parse_mode='Markdown'
                        )
                        await asyncio.sleep(retry_delay)
                    
                    session = await self.get_session()
                    
                    # Set headers for resume
                    headers = {}
                    if total_downloaded > 0:
                        headers['Range'] = f'bytes={total_downloaded}-'
                    
                    # Download with resume support
                    async with session.get(download_url, allow_redirects=True, headers=headers) as response:
                        logger.info(f"📥 Response status (attempt {attempt + 1}): {response.status}")
                        
                        if response.status in [200, 206]:  # 200 = full, 206 = partial
                            # Get total file size
                            if response.status == 206:
                                # Partial content - get total from Content-Range
                                content_range = response.headers.get('content-range', '')
                                if '/' in content_range:
                                    total_size = int(content_range.split('/')[-1])
                                else:
                                    total_size = int(response.headers.get('content-length', 0)) + total_downloaded
                            else:
                                # Full content
                                total_size = int(response.headers.get('content-length', 0))
                            
                            logger.info(f"📦 Total size: {self._format_bytes(total_size)}")
                            logger.info(f"📊 Resuming from: {self._format_bytes(total_downloaded)}")
                            
                            downloaded = total_downloaded
                            last_update = 0
                            start_time = asyncio.get_event_loop().time()
                            
                            # Even smaller chunks for stability (16KB)
                            chunk_size = 16 * 1024  # 16KB chunks
                            
                            try:
                                # Open in append mode if resuming
                                file_mode = 'ab' if total_downloaded > 0 else 'wb'
                                
                                async with aiofiles.open(file_path, file_mode) as file:
                                    chunk_count = 0
                                    async for chunk in response.content.iter_chunked(chunk_size):
                                        await file.write(chunk)
                                        downloaded += len(chunk)
                                        chunk_count += 1
                                        
                                        # Update progress every 50 chunks (800KB) or every 5 seconds
                                        if (chunk_count % 50 == 0 or 
                                            downloaded - last_update >= 5*1024*1024 or 
                                            downloaded >= total_size):
                                            
                                            last_update = downloaded
                                            current_time = asyncio.get_event_loop().time()
                                            elapsed = current_time - start_time
                                            
                                            if total_size > 0 and elapsed > 0:
                                                progress = (downloaded / total_size) * 100
                                                speed = (downloaded - total_downloaded) / elapsed if elapsed > 0 else 0
                                                speed_mb = speed / (1024 * 1024)
                                                
                                                try:
                                                    await status_msg.edit_text(
                                                        f"🚀 **Resumable Download**\n\n"
                                                        f"📊 **Progress:** {progress:.1f}%\n"
                                                        f"💾 **Downloaded:** {self._format_bytes(downloaded)}\n"
                                                        f"📦 **Total:** {self._format_bytes(total_size)}\n"
                                                        f"⚡ **Speed:** {speed_mb:.1f} MB/s\n"
                                                        f"🔄 **Attempt:** {attempt + 1}\n"
                                                        f"📡 **Chunks:** 16KB stable",
                                                        parse_mode='Markdown'
                                                    )
                                                except:
                                                    pass
                                
                                # Verify download completion
                                actual_size = os.path.getsize(file_path)
                                logger.info(f"✅ Download attempt completed: {self._format_bytes(actual_size)}")
                                
                                if total_size > 0 and actual_size >= total_size * 0.98:  # 98%+ is good
                                    logger.info(f"🎉 Download successful: {actual_size}/{total_size} bytes")
                                    return file_path
                                else:
                                    logger.warning(f"⚠️ Partial download: {actual_size}/{total_size} bytes")
                                    # Continue to next attempt (will resume from where it left off)
                                    continue
                                
                            except (asyncio.IncompleteReadError, aiohttp.ClientPayloadError, 
                                   ConnectionResetError, asyncio.TimeoutError) as conn_error:
                                logger.warning(f"⚠️ Connection error (attempt {attempt + 1}): {conn_error}")
                                # File is kept for resume - continue to next attempt
                                continue
                                
                            except Exception as file_error:
                                logger.error(f"❌ File error (attempt {attempt + 1}): {file_error}")
                                continue
                        
                        elif response.status == 416:
                            # Range not satisfiable - file already complete
                            if os.path.exists(file_path):
                                actual_size = os.path.getsize(file_path)
                                logger.info(f"✅ File already complete: {self._format_bytes(actual_size)}")
                                return file_path
                            else:
                                logger.error("❌ Range error with no file")
                                continue
                                
                        else:
                            logger.error(f"❌ HTTP error (attempt {attempt + 1}): {response.status}")
                            if attempt < max_retries - 1:
                                continue
                            else:
                                await status_msg.edit_text(
                                    f"❌ **Server Error**\n\n"
                                    f"HTTP {response.status} after {max_retries} attempts.\n"
                                    f"Server may be overloaded.\n\n"
                                    f"Please try again later!",
                                    parse_mode='Markdown'
                                )
                                return None
                                
                except Exception as e:
                    logger.error(f"❌ Exception (attempt {attempt + 1}): {e}")
                    continue
            
            # All attempts failed
            if os.path.exists(file_path):
                partial_size = os.path.getsize(file_path)
                await status_msg.edit_text(
                    f"❌ **Download Failed After {max_retries} Attempts**\n\n"
                    f"📁 **File:** {filename[:25]}...\n"
                    f"📊 **Partial:** {self._format_bytes(partial_size)} downloaded\n"
                    f"🔄 **Issue:** Connection keeps dropping\n\n"
                    f"**The server appears unstable.**\n"
                    f"Please try again later!",
                    parse_mode='Markdown'
                )
            else:
                await status_msg.edit_text(
                    "❌ **Connection Completely Failed**\n\n"
                    "Unable to establish stable connection.\n"
                    "The download server may be down.\n\n"
                    "Please try again later!",
                    parse_mode='Markdown'
                )
            
            return None
            
        except Exception as e:
            logger.error(f"❌ Fatal download error: {e}")
            await status_msg.edit_text(
                "❌ **System Error**\n\n"
                "A fatal error occurred during download.\n"
                "Please try again!",
                parse_mode='Markdown'
            )
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
        """Close session"""
        if self.session:
            await self.session.close()
                                
