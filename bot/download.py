"""
Complete Download Module - WDZone API Compatible
"""
import os
import asyncio
import aiohttp
import aiofiles
import urllib.parse
from loguru import logger
import config

async def get_download_info(terabox_url: str):
    """Get download information from WDZone API with correct response handling"""
    
    # Properly encode the URL
    encoded_url = urllib.parse.quote(terabox_url, safe=':/?#[]@!$&\'()*+,;=')
    api_url = f"https://wdzone-terabox-api.vercel.app/file_info?url={encoded_url}"
    
    logger.info(f"🔄 API Request: {api_url[:100]}...")
    
    timeout = aiohttp.ClientTimeout(total=30)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'en-US,en;q=0.9'
    }
    
    async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
        try:
            async with session.get(api_url) as response:
                logger.info(f"📡 API Response Status: {response.status}")
                
                if response.status == 200:
                    data = await response.json()
                    logger.info(f"📊 API Response Keys: {list(data.keys())}")
                    
                    # Handle WDZone API format from your screenshot
                    if data.get("Status") == "Success" and data.get("ExctractedInfo"):
                        extracted_info = data["ExctractedInfo"]
                        
                        if isinstance(extracted_info, list) and len(extracted_info) > 0:
                            file_info = extracted_info[0]  # Get first file
                        else:
                            file_info = extracted_info
                        
                        # Extract file details
                        file_name = file_info.get("Title", "unknown_file")
                        
                        # Handle size - could be string or number
                        size_str = file_info.get("Size", "0")
                        try:
                            if isinstance(size_str, str):
                                # Remove any non-numeric characters except decimal point
                                import re
                                size_clean = re.sub(r'[^\d.]', '', size_str)
                                file_size = int(float(size_clean) * 1024 * 1024)  # Convert MB to bytes
                            else:
                                file_size = int(size_str)
                        except:
                            file_size = 0
                        
                        # Get download links
                        download_links = file_info.get("DownloadLink", [])
                        if not download_links:
                            # Try alternative field names
                            download_links = (file_info.get("download_links") or 
                                            file_info.get("links") or 
                                            file_info.get("urls") or [])
                        
                        # Select best download URL
                        download_url = None
                        if isinstance(download_links, list) and len(download_links) > 0:
                            # Prefer the first link (usually highest quality)
                            download_url = download_links[0]
                        elif isinstance(download_links, str):
                            download_url = download_links
                        
                        if download_url and file_name:
                            size_mb = file_size / (1024 * 1024) if file_size else 0
                            logger.info(f"✅ WDZone API Success - File: {file_name}, Size: {size_mb:.2f} MB")
                            logger.info(f"🔗 Download URL: {download_url[:100]}...")
                            
                            return {
                                "file_name": file_name,
                                "file_size": file_size, 
                                "download_url": download_url
                            }
                    
                    # Fallback: Try old format
                    elif data.get("ok") and data.get("file_info"):
                        file_info = data["file_info"]
                        file_name = file_info.get("file_name", "unknown_file")
                        file_size = file_info.get("size", 0)
                        download_url = file_info.get("download_url")
                        
                        if download_url:
                            size_mb = file_size / (1024 * 1024) if file_size else 0
                            logger.info(f"✅ Legacy API Success - File: {file_name}, Size: {size_mb:.2f} MB")
                            
                            return {
                                "file_name": file_name,
                                "file_size": file_size, 
                                "download_url": download_url
                            }
                    
                    logger.error(f"❌ API returned unexpected format: {str(data)[:500]}...")
                    raise Exception("API response format not recognized")
                    
                else:
                    response_text = await response.text()
                    logger.error(f"❌ API request failed with status {response.status}: {response_text[:200]}...")
                    raise Exception(f"API request failed: {response.status}")
                    
        except aiohttp.ClientError as e:
            logger.error(f"❌ Network error: {e}")
            raise Exception(f"Network error: {e}")
        except Exception as e:
            logger.error(f"❌ API request error: {e}")
            raise

def _sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    import re
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    # Replace multiple spaces with single space
    filename = re.sub(r'\s+', ' ', filename).strip()
    # Limit length
    if len(filename) > 200:
        name, ext = os.path.splitext(filename)
        filename = name[:190] + ext
    return filename

async def download_file(download_url: str, filename: str, status_msg):
    """Download file with multiple fallback strategies"""
    filename = _sanitize_filename(filename)
    file_path = os.path.join(config.DOWNLOAD_DIR, filename)
    os.makedirs(config.DOWNLOAD_DIR, exist_ok=True)
    
    logger.info(f"📥 Starting download: {filename}")
    logger.info(f"🔗 Download URL: {download_url[:100]}...")
    
    # Strategy 1: Large chunks with proper headers
    try:
        await status_msg.edit_text("📥 Downloading with optimized settings...", parse_mode=None)
        logger.info("🔄 Attempting optimized download")
        
        timeout = aiohttp.ClientTimeout(total=600, sock_read=120)  # 10 minutes total, 2 min read
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        }
        
        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            async with session.get(download_url) as response:
                logger.info(f"📡 Download Response Status: {response.status}")
                
                if response.status == 200:
                    content_length = response.headers.get('Content-Length')
                    if content_length:
                        total_size = int(content_length)
                        logger.info(f"📊 File size from headers: {total_size / (1024*1024):.2f} MB")
                    
                    async with aiofiles.open(file_path, 'wb') as file:
                        downloaded = 0
                        chunk_size = 1024 * 256  # 256KB chunks
                        
                        async for chunk in response.content.iter_chunked(chunk_size):
                            await file.write(chunk)
                            downloaded += len(chunk)
                            
                            # Update progress every 5MB
                            if downloaded % (5 * 1024 * 1024) == 0:
                                mb_downloaded = downloaded / (1024 * 1024)
                                logger.info(f"📥 Progress: {mb_downloaded:.1f} MB downloaded")
                                try:
                                    await status_msg.edit_text(f"📥 Downloaded: {mb_downloaded:.1f} MB...", parse_mode=None)
                                except:
                                    pass  # Ignore edit errors
                    
                    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                        final_size = os.path.getsize(file_path) / (1024 * 1024)
                        logger.info(f"✅ Download successful! Final size: {final_size:.2f} MB")
                        return file_path
                        
                else:
                    logger.error(f"❌ Download failed with status {response.status}")
                    
    except Exception as e:
        logger.warning(f"Optimized download failed: {e}")
    
    # Strategy 2: Conservative approach
    try:
        await status_msg.edit_text("📥 Retrying with conservative settings...", parse_mode=None)
        logger.info("🔄 Attempting conservative download")
        
        timeout = aiohttp.ClientTimeout(total=300, sock_read=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(download_url) as response:
                if response.status == 200:
                    async with aiofiles.open(file_path, 'wb') as file:
                        chunk_size = 1024 * 64  # 64KB chunks
                        async for chunk in response.content.iter_chunked(chunk_size):
                            await file.write(chunk)
                            await asyncio.sleep(0.01)  # Small delay
                    
                    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                        logger.info("✅ Conservative download successful!")
                        return file_path
                        
    except Exception as e:
        logger.warning(f"Conservative download failed: {e}")
    
    # Strategy 3: Ultra-safe approach
    try:
        await status_msg.edit_text("📥 Final attempt with ultra-safe settings...", parse_mode=None)
        logger.info("🔄 Attempting ultra-safe download")
        
        timeout = aiohttp.ClientTimeout(total=900, sock_read=180)  # 15 minutes total, 3 min read
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(download_url) as response:
                if response.status == 200:
                    async with aiofiles.open(file_path, 'wb') as file:
                        chunk_size = 1024 * 8  # 8KB chunks
                        async for chunk in response.content.iter_chunked(chunk_size):
                            await file.write(chunk)
                            await asyncio.sleep(0.1)  # Longer delay for stability
                    
                    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                        logger.info("✅ Ultra-safe download successful!")
                        return file_path
                        
    except Exception as e:
        logger.error(f"Ultra-safe download failed: {e}")
    
    # All strategies failed
    logger.error("❌ All download strategies failed")
    return None

# TeraboxDownloader class for backward compatibility
class TeraboxDownloader:
    """Compatibility class for existing handlers"""
    
    def __init__(self):
        pass
    
    async def get_session(self):
        """Dummy method for compatibility"""
        pass
    
    async def close_session(self):
        """Dummy method for compatibility"""
        pass
    
    async def get_download_info(self, terabox_url: str, *args, **kwargs):
        """Get download info - flexible parameter handling"""
        return await get_download_info(terabox_url)
    
    async def download_with_resume(self, download_url: str, filename: str, status_msg, *args, **kwargs):
        """Download with resume - flexible parameter handling"""
        return await download_file(download_url, filename, status_msg)

# Create global instance for backward compatibility
downloader = TeraboxDownloader()
                                
