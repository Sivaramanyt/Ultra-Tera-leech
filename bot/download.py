"""
Download functionality - High-Speed Optimized Complete Version (Part 1)
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
        """Get optimized HTTP session with high-speed settings"""
        if not self.session or self.session.closed:
            connector = aiohttp.TCPConnector(
                limit=100,               # Increased connection pool
                limit_per_host=10,       # More connections per host
                ttl_dns_cache=300,
                use_dns_cache=True,
                keepalive_timeout=90,    # Longer keepalive
                enable_cleanup_closed=True,
                force_close=False        # Keep connections alive
            )
            
            timeout = aiohttp.ClientTimeout(
                total=1800,      # 30 minutes total
                connect=15,      # Faster connect timeout
                sock_read=180,   # 3 minutes for reading
                sock_connect=15  # 15 seconds socket connect
            )
            
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
                    'Accept': '*/*',
                    'Accept-Encoding': 'gzip, deflate',
                    'Connection': 'keep-alive'
                }
            )
        
        return self.session
    
    async def get_download_info(self, url: str, status_msg):
        """Get download URL and file info from WDZone API"""
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
                params = {'url': terabox_url}
                logger.info(f"📤 Making request to: {api_url} with params: {params}")
                
                async with session.get(api_url, params=params) as response:
                    logger.info(f"📥 Response status: {response.status}")
                    
                    if response.status == 200:
                        try:
                            result = await response.json()
                            logger.info(f"📋 WDZone API response keys: {list(result.keys())}")
                            
                            # Find status and info fields
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
                                                    logger.info(f"🔗 Found download URL in field: {key}")
                                                
                                                if 'title' in key.lower() or 'name' in key.lower():
                                                    title = value
                                                    logger.info(f"📄 Found title in field: {key}")
                                                
                                                if 'size' in key.lower():
                                                    size = value
                                                    logger.info(f"📏 Found size in field: {key}")
                                        
                                        if download_url:
                                            return {
                                                'success': True,
                                                'download_url': download_url,
                                                'filename': title,
                                                'size': size
                                            }
                        
                        except Exception as json_error:
                            logger.error(f"❌ JSON parsing error: {json_error}")
                    else:
                        logger.error(f"❌ HTTP error: {response.status}")
            
            return {'success': False, 'error': f'No download URL from {api_type}'}
            
        except Exception as e:
            logger.error(f"💥 API {api_type} error: {e}")
            return {'success': False, 'error': f'{api_type} API error: {str(e)}'}
    
    async def download_file(self, download_url: str, filename: str, status_msg):
        """High-speed optimized download with parallel chunks"""
        try:
            filename = self._sanitize_filename(filename)
            file_path = os.path.join(config.DOWNLOAD_DIR, filename)
            os.makedirs(config.DOWNLOAD_DIR, exist_ok=True)
            
            logger.info(f"🚀 Starting high-speed download: {file_path}")
            
            # Get file info first
            session = await self.get_session()
            
            # Check if server supports range requests
            try:
                async with session.head(download_url) as head_response:
                    supports_ranges = head_response.headers.get('Accept-Ranges') == 'bytes'
                    total_size = int(head_response.headers.get('content-length', 0))
                    
                    logger.info(f"📊 File size: {self._format_bytes(total_size)}, Ranges: {supports_ranges}")
            except:
                supports_ranges = False
                total_size = 0
            
            # Choose download strategy
            if supports_ranges and total_size > 5 * 1024 * 1024:  # 5MB+
                logger.info("🔥 Using parallel chunk download for maximum speed")
                return await self._parallel_download(download_url, file_path, total_size, status_msg)
            else:
                logger.info("⚡ Using optimized single-stream download")
                return await self._optimized_download(download_url, file_path, status_msg)
                
        except Exception as e:
            logger.error(f"Download error: {e}")
            return None
     async def _parallel_download(self, download_url: str, file_path: str, total_size: int, status_msg):
        """Download file using parallel chunks for maximum speed"""
        try:
            session = await self.get_session()
            
            # Calculate optimal chunk size and thread count
            min_chunk_size = 1024 * 1024  # 1MB minimum
            max_chunks = 8  # Maximum parallel downloads
            
            # Dynamic chunk calculation based on file size
            if total_size < 50 * 1024 * 1024:  # < 50MB
                chunk_size = max(min_chunk_size, total_size // 4)
                num_chunks = min(4, max(2, total_size // chunk_size))
            else:  # >= 50MB
                chunk_size = max(min_chunk_size * 2, total_size // max_chunks)
                num_chunks = min(max_chunks, max(4, total_size // chunk_size))
            
            logger.info(f"🔥 Parallel download: {num_chunks} chunks of {self._format_bytes(chunk_size)}")
            
            await status_msg.edit_text(
                f"🚀 **High-Speed Parallel Download**\n\n"
                f"📁 **File:** {os.path.basename(file_path)[:30]}...\n"
                f"📦 **Size:** {self._format_bytes(total_size)}\n"
                f"⚡ **Threads:** {num_chunks} parallel downloads\n"
                f"🔥 **Mode:** Maximum Speed",
                parse_mode='Markdown'
            )
            
            # Create download tasks
            tasks = []
            chunk_files = []
            
            for i in range(num_chunks):
                start = i * chunk_size
                if i == num_chunks - 1:  # Last chunk gets remainder
                    end = total_size - 1
                else:
                    end = start + chunk_size - 1
                
                chunk_file = f"{file_path}.part{i}"
                chunk_files.append(chunk_file)
                
                task = asyncio.create_task(
                    self._download_chunk(session, download_url, start, end, chunk_file, i)
                )
                tasks.append(task)
            
            # Track progress with enhanced monitoring
            start_time = asyncio.get_event_loop().time()
            completed = 0
            total_downloaded = 0
            
            while completed < len(tasks):
                await asyncio.sleep(0.5)  # Check twice per second
                
                # Check completed tasks and calculate progress
                new_completed = sum(1 for task in tasks if task.done())
                
                # Calculate downloaded bytes from existing chunk files
                current_downloaded = 0
                for chunk_file in chunk_files:
                    if os.path.exists(chunk_file):
                        current_downloaded += os.path.getsize(chunk_file)
                
                if new_completed > completed or current_downloaded > total_downloaded:
                    completed = new_completed
                    total_downloaded = current_downloaded
                    
                    progress = (total_downloaded / total_size * 100) if total_size > 0 else 0
                    elapsed = asyncio.get_event_loop().time() - start_time
                    speed = total_downloaded / elapsed if elapsed > 0 else 0
                    speed_mb = speed / (1024 * 1024)
                    
                    try:
                        await status_msg.edit_text(
                            f"🚀 **High-Speed Parallel Download**\n\n"
                            f"📊 **Progress:** {progress:.1f}%\n"
                            f"💾 **Downloaded:** {self._format_bytes(total_downloaded)}\n"
                            f"📦 **Total:** {self._format_bytes(total_size)}\n"
                            f"⚡ **Speed:** {speed_mb:.1f} MB/s\n"
                            f"🔥 **Chunks:** {completed}/{len(tasks)} complete",
                            parse_mode='Markdown'
                        )
                    except:
                        pass
            
            # Wait for all tasks to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Check if all downloads succeeded
            failed_chunks = sum(1 for result in results if not result or isinstance(result, Exception))
            if failed_chunks > 0:
                logger.warning(f"⚠️ {failed_chunks} chunks failed, attempting fallback")
                return await self._optimized_download(download_url, file_path, status_msg)
            
            # Combine chunks into final file
            await self._combine_chunks(chunk_files, file_path)
            
            # Cleanup chunk files
            for chunk_file in chunk_files:
                try:
                    os.remove(chunk_file)
                except:
                    pass
            
            elapsed_time = asyncio.get_event_loop().time() - start_time
            avg_speed = total_size / elapsed_time / (1024 * 1024) if elapsed_time > 0 else 0
            logger.info(f"✅ Parallel download completed: {file_path} ({avg_speed:.1f} MB/s)")
            
            return file_path
            
        except Exception as e:
            logger.error(f"Parallel download error: {e}")
            # Fallback to single stream
            return await self._optimized_download(download_url, file_path, status_msg)
    
    async def _download_chunk(self, session, url: str, start: int, end: int, chunk_file: str, chunk_id: int):
        """Download a specific chunk of the file with retry logic"""
        max_retries = 3
        
        for attempt in range(max_retries):
            try:
                headers = {'Range': f'bytes={start}-{end}'}
                logger.info(f"📥 Downloading chunk {chunk_id}: bytes {start}-{end} (attempt {attempt + 1})")
                
                async with session.get(url, headers=headers) as response:
                    if response.status in [200, 206]:
                        async with aiofiles.open(chunk_file, 'wb') as f:
                            async for chunk in response.content.iter_chunked(65536):  # 64KB chunks
                                await f.write(chunk)
                        
                        # Verify chunk size
                        actual_size = os.path.getsize(chunk_file)
                        expected_size = end - start + 1
                        
                        if actual_size == expected_size:
                            logger.info(f"✅ Chunk {chunk_id} completed successfully")
                            return True
                        else:
                            logger.warning(f"⚠️ Chunk {chunk_id} size mismatch: {actual_size} vs {expected_size}")
                    else:
                        logger.error(f"❌ Chunk {chunk_id} HTTP error: {response.status}")
                        
            except Exception as e:
                logger.warning(f"⚠️ Chunk {chunk_id} attempt {attempt + 1} failed: {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)  # Wait before retry
                    continue
        
        logger.error(f"❌ Chunk {chunk_id} failed after {max_retries} attempts")
        return False
    
    async def _combine_chunks(self, chunk_files: list, output_file: str):
        """Combine downloaded chunks into final file with verification"""
        try:
            logger.info(f"🔧 Combining {len(chunk_files)} chunks into {output_file}")
            
            async with aiofiles.open(output_file, 'wb') as output:
                for i, chunk_file in enumerate(chunk_files):
                    if os.path.exists(chunk_file):
                        chunk_size = os.path.getsize(chunk_file)
                        logger.info(f"📄 Combining chunk {i}: {self._format_bytes(chunk_size)}")
                        
                        async with aiofiles.open(chunk_file, 'rb') as chunk:
                            while True:
                                data = await chunk.read(1024 * 1024)  # 1MB buffer
                                if not data:
                                    break
                                await output.write(data)
                    else:
                        logger.error(f"❌ Chunk file missing: {chunk_file}")
                        raise FileNotFoundError(f"Chunk {i} is missing")
            
            # Verify final file
            final_size = os.path.getsize(output_file)
            logger.info(f"✅ Combined file size: {self._format_bytes(final_size)}")
            
        except Exception as e:
            logger.error(f"Chunk combination error: {e}")
            raise
    
    async def _optimized_download(self, download_url: str, file_path: str, status_msg):
        """Optimized single-stream download with enhanced performance"""
        try:
            session = await self.get_session()
            
            async with session.get(download_url) as response:
                if response.status == 200:
                    total_size = int(response.headers.get('content-length', 0))
                    downloaded = 0
                    last_update = 0
                    start_time = asyncio.get_event_loop().time()
                    
                    # Use larger buffer for better performance
                    chunk_size = 128 * 1024  # 128KB chunks
                    
                    async with aiofiles.open(file_path, 'wb') as file:
                        async for chunk in response.content.iter_chunked(chunk_size):
                            await file.write(chunk)
                            downloaded += len(chunk)
                            
                            # Update progress every 1MB or 10% of file
                            update_interval = min(1024*1024, max(102400, total_size // 10))
                            
                            if downloaded - last_update >= update_interval or downloaded >= total_size:
                                last_update = downloaded
                                current_time = asyncio.get_event_loop().time()
                                elapsed = current_time - start_time
                                
                                if total_size > 0 and elapsed > 0:
                                    progress = (downloaded / total_size) * 100
                                    speed = downloaded / elapsed
                                    speed_mb = speed / (1024 * 1024)
                                    eta = (total_size - downloaded) / speed if speed > 0 else 0
                                    
                                    try:
                                        await status_msg.edit_text(
                                            f"📥 **Optimized High-Speed Download**\n\n"
                                            f"📊 **Progress:** {progress:.1f}%\n"
                                            f"💾 **Downloaded:** {self._format_bytes(downloaded)}\n"
                                            f"📦 **Total:** {self._format_bytes(total_size)}\n"
                                            f"🚀 **Speed:** {speed_mb:.1f} MB/s\n"
                                            f"⏱️ **ETA:** {eta:.0f}s",
                                            parse_mode='Markdown'
                                        )
                                    except:
                                        pass
                    
                    elapsed_time = asyncio.get_event_loop().time() - start_time
                    avg_speed = downloaded / elapsed_time / (1024 * 1024) if elapsed_time > 0 else 0
                    logger.info(f"✅ Optimized download completed: {file_path} ({avg_speed:.1f} MB/s)")
                    
                    return file_path
                else:
                    logger.error(f"❌ Download failed: HTTP {response.status}")
                    return None
                    
        except Exception as e:
            logger.error(f"Optimized download error: {e}")
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
        """Close session and cleanup"""
        if self.session:
            await self.session.close()
                                  
