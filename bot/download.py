"""

Complete Download Module - ULTRA-FAST OPTIMIZED FIXED (Part 1)

"""

import os
import asyncio
import aiohttp
import aiofiles
import urllib.parse
from loguru import logger
import config

async def get_download_info(terabox_url: str, status_msg=None):
    """Get download information from WDZone API with compatible return format"""
    try:
        # Properly encode the URL
        encoded_url = urllib.parse.quote(terabox_url, safe='')
        api_url = f"https://wdzone-terabox-api.vercel.app/api?url={encoded_url}"
        logger.info(f"🔄 API Request: {api_url[:100]}...")
        
        # Enhanced timeout for API requests
        timeout = aiohttp.ClientTimeout(total=60, connect=15, sock_read=30)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'application/json, text/plain, */*',
            'Accept-Language': 'en-US,en;q=0.9'
        }

        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            async with session.get(api_url) as response:
                logger.info(f"📡 API Response Status: {response.status}")
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"📊 API Response Keys: {list(data.keys())}")
                    
                    # Handle WDZone API format
                    status_key = None
                    extracted_key = None
                    
                    # Find status key (with or without emoji)
                    for key in data.keys():
                        if "Status" in key or "status" in key:
                            status_key = key
                        if "Extracted" in key or "extracted" in key:
                            extracted_key = key
                    
                    if status_key and data.get(status_key) == "Success" and extracted_key:
                        extracted_info = data[extracted_key]
                        if isinstance(extracted_info, list) and len(extracted_info) > 0:
                            file_info = extracted_info[0]
                        else:
                            file_info = extracted_info
                        
                        # Extract file details (handle emoji keys)
                        file_name = None
                        file_size_str = None
                        download_url = None
                        
                        # Find title/name key
                        for key, value in file_info.items():
                            if "Title" in key or "title" in key or "name" in key:
                                file_name = value
                            elif "Size" in key or "size" in key:
                                file_size_str = value
                            elif "Direct" in key or "download" in key or "link" in key:
                                download_url = value
                        
                        # Default fallback if keys not found
                        if not file_name:
                            file_name = file_info.get("Title", file_info.get("title", "unknown_file"))
                        if not file_size_str:
                            file_size_str = file_info.get("Size", file_info.get("size", "0"))
                        if not download_url:
                            download_url = file_info.get("Direct Download Link", file_info.get("download_url"))
                        
                        # Handle size conversion for numeric value
                        try:
                            if isinstance(file_size_str, str):
                                import re
                                # Extract number from "30.56 MB" format
                                size_match = re.search(r'([\d.]+)', file_size_str)
                                if size_match:
                                    size_num = float(size_match.group(1))
                                    if "MB" in file_size_str.upper():
                                        file_size = int(size_num * 1024 * 1024)
                                    elif "GB" in file_size_str.upper():
                                        file_size = int(size_num * 1024 * 1024 * 1024)
                                    elif "KB" in file_size_str.upper():
                                        file_size = int(size_num * 1024)
                                    else:
                                        file_size = int(size_num)
                                else:
                                    file_size = 0
                            else:
                                file_size = int(file_size_str)
                        except:
                            file_size = 0
                        
                        if download_url and file_name:
                            size_mb = file_size / (1024 * 1024) if file_size else 0
                            logger.info(f"✅ WDZone API Success - File: {file_name}, Size: {size_mb:.2f} MB")
                            logger.info(f"🔗 Download URL: {download_url[:100]}...")
                            
                            # Return in the format handlers expect
                            return {
                                "success": True,
                                "filename": file_name,
                                "size": file_size_str,  # Keep original size string
                                "download_url": download_url,
                                "file_size": file_size  # Also provide numeric size
                            }
                    
                    logger.error(f"❌ API returned unexpected format: {str(data)[:500]}...")
                    return {
                        "success": False,
                        "error": "API response format not recognized"
                    }
                else:
                    response_text = await response.text()
                    logger.error(f"❌ API request failed with status {response.status}: {response_text[:200]}...")
                    return {
                        "success": False,
                        "error": f"API request failed: {response.status}"
                    }
    except Exception as e:
        logger.error(f"❌ API request error: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def _sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    import re
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    filename = re.sub(r'\s+', ' ', filename).strip()
    if len(filename) > 200:
        name, ext = os.path.splitext(filename)
        filename = name[:190] + ext
    return filename

async def download_chunk_with_retry(url: str, start: int, end: int, chunk_id: int, max_retries: int = 3):
    """Download a specific chunk with retry logic"""
    for attempt in range(max_retries):
        try:
            headers = {
                'Range': f'bytes={start}-{end}',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': '*/*',
                'Connection': 'keep-alive'
            }
            
            # Progressive timeout increase on retries
            timeout_total = 200 + (attempt * 60)  # 200s, 260s, 320s
            timeout = aiohttp.ClientTimeout(total=timeout_total, sock_read=90, connect=15)
            
            connector = aiohttp.TCPConnector(
                limit=10,
                limit_per_host=3,
                enable_cleanup_closed=True,
                keepalive_timeout=30
            )
            
            async with aiohttp.ClientSession(timeout=timeout, connector=connector) as session:
                async with session.get(url, headers=headers) as response:
                    if response.status in [206, 200]:  # Partial or full content
                        data = await response.read()
                        logger.info(f"📦 Chunk {chunk_id}: {len(data)/(1024*1024):.1f} MB downloaded (attempt {attempt + 1})")
                        return chunk_id, data
                    else:
                        logger.warning(f"⚠️ Chunk {chunk_id} failed: status {response.status} (attempt {attempt + 1})")
        except aiohttp.ClientPayloadError as e:
            logger.warning(f"🔄 Chunk {chunk_id} payload error (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        except Exception as e:
            logger.error(f"❌ Chunk {chunk_id} error (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 ** attempt)
    
    return chunk_id, None

async def download_chunk(url: str, start: int, end: int, chunk_id: int):
    """Download a specific chunk of the file in parallel - Enhanced"""
    return await download_chunk_with_retry(url, start, end, chunk_id)

async def download_parallel_chunks(download_url: str, file_path: str, total_size: int, status_msg):
    """PARALLEL DOWNLOAD: Download file in multiple chunks simultaneously - Enhanced"""
    try:
        # Smart chunk calculation
        if total_size < 10 * 1024 * 1024:  # < 10MB
            chunk_count = 2
        elif total_size < 30 * 1024 * 1024:  # < 30MB
            chunk_count = 3
        else:  # >= 30MB
            chunk_count = 4
        
        chunk_size = total_size // chunk_count
        logger.info(f"🔥 PARALLEL: {chunk_count} chunks × {chunk_size/(1024*1024):.1f} MB")
        
        tasks = []
        for i in range(chunk_count):
            start = i * chunk_size
            end = start + chunk_size - 1 if i < chunk_count - 1 else total_size - 1
            task = download_chunk(download_url, start, end, i)
            tasks.append(task)
        
        # Download chunks in parallel
        await status_msg.edit_text(f"🔥 Parallel downloading {chunk_count} chunks...", parse_mode=None)
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        valid_chunks = []
        for result in results:
            if isinstance(result, tuple) and result[1] is not None:
                valid_chunks.append(result)
        
        if len(valid_chunks) == chunk_count:
            # Sort by chunk ID and combine
            valid_chunks.sort(key=lambda x: x[0])
            with open(file_path, 'wb') as outfile:
                for chunk_id, chunk_data in valid_chunks:
                    outfile.write(chunk_data)
            
            if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                final_size = os.path.getsize(file_path) / (1024 * 1024)
                logger.info(f"✅ PARALLEL SUCCESS: {final_size:.2f} MB")
                return file_path
        else:
            logger.warning(f"⚠️ Parallel incomplete: {len(valid_chunks)}/{chunk_count}")
    
    except Exception as e:
        logger.error(f"❌ Parallel download failed: {e}")
    
    return None

async def download_with_enhanced_retry(download_url: str, file_path: str, chunk_size: int, status_msg, strategy_name: str, max_retries: int = 3):
    """Enhanced download with retry logic and session recreation"""
    for attempt in range(max_retries):
        try:
            # Progressive timeout configuration
            base_timeout = 300 + (attempt * 120)  # 300s, 420s, 540s
            timeout = aiohttp.ClientTimeout(
                total=base_timeout,
                sock_read=60 + (attempt * 30),  # 60s, 90s, 120s
                sock_connect=15 + (attempt * 5)  # 15s, 20s, 25s
            )
            
            connector = aiohttp.TCPConnector(
                limit=20 - (attempt * 5),  # Reduce connections on retry
                limit_per_host=5 - attempt,
                ttl_dns_cache=300,
                use_dns_cache=True,
                keepalive_timeout=60,
                enable_cleanup_closed=True
            )
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': '*/*',
                'Accept-Language': 'en-US,en;q=0.9',
                'Connection': 'keep-alive',
                'Accept-Encoding': 'gzip, deflate, br'
            }
            
            logger.info(f"🔄 {strategy_name} download attempt {attempt + 1}/{max_retries}")
            await status_msg.edit_text(f"{strategy_name} downloading... (attempt {attempt + 1})", parse_mode=None)
            
            async with aiohttp.ClientSession(timeout=timeout, headers=headers, connector=connector) as session:
                async with session.get(download_url) as response:
                    logger.info(f"📡 Download Response Status: {response.status}")
                    
                    if response.status == 200:
                        content_length = response.headers.get('Content-Length')
                        if content_length:
                            total_size = int(content_length)
                            total_mb = total_size / (1024*1024)
                            logger.info(f"📊 File size: {total_mb:.2f} MB")
                        
                        async with aiofiles.open(file_path, 'wb') as file:
                            downloaded = 0
                            start_time = asyncio.get_event_loop().time()
                            last_update = start_time
                            
                            async for chunk in response.content.iter_chunked(chunk_size):
                                await file.write(chunk)
                                downloaded += len(chunk)
                                
                                current_time = asyncio.get_event_loop().time()
                                if current_time - last_update >= 3:  # Update every 3 seconds
                                    mb_downloaded = downloaded / (1024 * 1024)
                                    elapsed = current_time - start_time
                                    speed = downloaded / elapsed / (1024 * 1024) if elapsed > 0 else 0
                                    logger.info(f"🚀 {strategy_name}: {mb_downloaded:.1f} MB @ {speed:.1f} MB/s")
                                    
                                    try:
                                        await status_msg.edit_text(f"🚀 Downloaded: {mb_downloaded:.1f} MB @ {speed:.1f} MB/s", parse_mode=None)
                                    except:
                                        pass
                                    last_update = current_time
                        
                        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                            final_size = os.path.getsize(file_path) / (1024 * 1024)
                            total_time = asyncio.get_event_loop().time() - start_time
                            avg_speed = final_size / total_time if total_time > 0 else 0
                            logger.info(f"✅ {strategy_name} success! {final_size:.2f} MB in {total_time:.1f}s @ {avg_speed:.1f} MB/s")
                            return file_path
                    
        except aiohttp.ClientPayloadError as e:
            logger.warning(f"🔄 {strategy_name} payload error (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(3 + (attempt * 2))  # Progressive backoff
        except asyncio.TimeoutError as e:
            logger.warning(f"⏰ {strategy_name} timeout (attempt {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 + attempt)
        except Exception as e:
            logger.warning(f"❌ {strategy_name} failed (attempt {attempt + 1}): {str(e)[:100]}")
            if attempt < max_retries - 1:
                await asyncio.sleep(2 + attempt)
    
    logger.error(f"❌ {strategy_name} failed after {max_retries} attempts")
    return None

async def download_file(download_url: str, filename: str, status_msg):
    """ULTRA-FAST Download - Enhanced with retry mechanisms"""
    filename = _sanitize_filename(filename)
    file_path = os.path.join(config.DOWNLOAD_DIR, filename)
    os.makedirs(config.DOWNLOAD_DIR, exist_ok=True)
    
    logger.info(f"🚀 Starting ULTRA-FAST download: {filename}")
    logger.info(f"🔗 Download URL: {download_url[:100]}...")
    
    # Strategy 1: PARALLEL CHUNK DOWNLOAD (if supported)
    try:
        await status_msg.edit_text("🔥 Testing parallel download...", parse_mode=None)
        logger.info("🔄 Testing parallel download capability")
        
        timeout = aiohttp.ClientTimeout(total=20, connect=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.head(download_url) as response:
                if response.status == 200:
                    accept_ranges = response.headers.get('Accept-Ranges', '').lower()
                    content_length = response.headers.get('Content-Length')
                    
                    if accept_ranges == 'bytes' and content_length:
                        total_size = int(content_length)
                        if total_size > 5 * 1024 * 1024:  # Only for files > 5MB
                            logger.info(f"🔥 Parallel supported! Size: {total_size/(1024*1024):.1f} MB")
                            result = await download_parallel_chunks(download_url, file_path, total_size, status_msg)
                            if result:
                                return result
                        else:
                            logger.info("📝 File too small for parallel download")
                    else:
                        logger.info("📝 Server doesn't support range requests")
    except Exception as e:
        logger.info(f"📝 Parallel not available: {str(e)[:100]}")
    
    # Strategy 2: ULTRA-FAST SINGLE STREAM (Enhanced)
    result = await download_with_enhanced_retry(
        download_url, file_path, 
        chunk_size=1024 * 1024 * 4,  # 4MB chunks
        status_msg=status_msg, 
        strategy_name="🚀 ULTRA-FAST"
    )
    if result:
        return result
    
    # Strategy 3: SUPER-FAST DOWNLOAD (Enhanced)
    result = await download_with_enhanced_retry(
        download_url, file_path,
        chunk_size=1024 * 1024 * 2,  # 2MB chunks 
        status_msg=status_msg,
        strategy_name="⚡ SUPER-FAST"
    )
    if result:
        return result
    
    # Strategy 4: CONSERVATIVE DOWNLOAD (Enhanced)
    result = await download_with_enhanced_retry(
        download_url, file_path,
        chunk_size=1024 * 512,  # 512KB chunks
        status_msg=status_msg,
        strategy_name="📥 CONSERVATIVE"
    )
    if result:
        return result
    
    # Strategy 5: MINIMAL CHUNKS (Final fallback)
    result = await download_with_enhanced_retry(
        download_url, file_path,
        chunk_size=1024 * 64,  # 64KB chunks
        status_msg=status_msg,
        strategy_name="🐌 MINIMAL"
    )
    if result:
        return result
    
    logger.error("❌ All download strategies failed")
    return None

# TeraboxDownloader class for backward compatibility
class TeraboxDownloader:
    """Compatibility class - ULTRA-FAST OPTIMIZED & FIXED"""
    
    def __init__(self):
        pass
    
    async def get_session(self):
        """Dummy method for compatibility"""
        pass
    
    async def close_session(self):
        """Dummy method for compatibility"""
        pass
    
    async def get_download_info(self, terabox_url: str, status_msg=None, *args, **kwargs):
        """Get download info - flexible parameter handling"""
        return await download_file(download_url, filename, status_msg)

    async def download_with_resume(self, download_url: str, filename: str, status_msg, *args, **kwargs):
        """Download with resume - flexible parameter handling"""
        return await download_file(download_url, filename, status_msg)
    
    async def download_file(self, download_url: str, filename: str, status_msg, *args, **kwargs):
        """Download file method - FIXED compatibility"""
        return await download_file(download_url, filename, status_msg)
    
    async def cleanup_file(self, file_path: str):
        """Clean up downloaded file - ASYNC COMPATIBLE"""
        try:
            if file_path and os.path.exists(file_path):
                os.remove(file_path)
                logger.info(f"🧹 Cleaned up file: {file_path}")
                return True
            else:
                logger.warning(f"⚠️ File not found for cleanup: {file_path}")
                return False
        except Exception as e:
            logger.warning(f"⚠️ Could not cleanup file {file_path}: {e}")
            return False

# Create global instance for backward compatibility
downloader = TeraboxDownloader()
