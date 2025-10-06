"""
Complete Download Module - ASYNC FIXED + SPEED OPTIMIZED
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
        
        timeout = aiohttp.ClientTimeout(total=30)
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
    """OPTIMIZED Download - PERFECT CHUNK SIZE (No More Payload Errors)"""
    filename = _sanitize_filename(filename)
    file_path = os.path.join(config.DOWNLOAD_DIR, filename)
    os.makedirs(config.DOWNLOAD_DIR, exist_ok=True)
    
    logger.info(f"⚡ Starting OPTIMIZED download: {filename}")
    logger.info(f"🔗 Download URL: {download_url[:100]}...")
    
    # Strategy 1: OPTIMIZED HIGH-SPEED (PERFECT CHUNK SIZE)
    try:
        await status_msg.edit_text("⚡ Optimized high-speed downloading...", parse_mode=None)
        logger.info("🔄 Attempting OPTIMIZED HIGH-SPEED download")
        
        timeout = aiohttp.ClientTimeout(total=300, sock_read=120)
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': '*/*',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive'
        }
        
        async with aiohttp.ClientSession(timeout=timeout, headers=headers) as session:
            async with session.get(download_url) as response:
                logger.info(f"📡 Download Response Status: {response.status}")
                
                if response.status == 200:
                    content_length = response.headers.get('Content-Length')
                    if content_length:
                        total_size = int(content_length)
                        total_mb = total_size / (1024*1024)
                        logger.info(f"📊 File size from headers: {total_mb:.2f} MB")
                    
                    async with aiofiles.open(file_path, 'wb') as file:
                        downloaded = 0
                        chunk_size = 1024 * 1024  # 1MB chunks - PERFECT SIZE!
                        
                        async for chunk in response.content.iter_chunked(chunk_size):
                            await file.write(chunk)
                            downloaded += len(chunk)
                            
                            # Update progress every 3MB
                            if downloaded % (3 * 1024 * 1024) == 0:
                                mb_downloaded = downloaded / (1024 * 1024)
                                logger.info(f"⚡ FAST Progress: {mb_downloaded:.1f} MB downloaded")
                                try:
                                    await status_msg.edit_text(f"⚡ Downloaded: {mb_downloaded:.1f} MB...", parse_mode=None)
                                except:
                                    pass  # Ignore edit errors
                    
                    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                        final_size = os.path.getsize(file_path) / (1024 * 1024)
                        logger.info(f"✅ OPTIMIZED HIGH-SPEED download successful! Final size: {final_size:.2f} MB")
                        return file_path
                        
                else:
                    logger.error(f"❌ Download failed with status {response.status}")
                    
    except Exception as e:
        logger.warning(f"Optimized high-speed download failed: {e}")
    
    # Strategy 2: MEDIUM-SPEED download
    try:
        await status_msg.edit_text("🚀 Medium-speed downloading...", parse_mode=None)
        logger.info("🔄 Attempting MEDIUM-SPEED download")
        
        timeout = aiohttp.ClientTimeout(total=600, sock_read=180)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(download_url) as response:
                if response.status == 200:
                    async with aiofiles.open(file_path, 'wb') as file:
                        chunk_size = 1024 * 512  # 512KB chunks
                        async for chunk in response.content.iter_chunked(chunk_size):
                            await file.write(chunk)
                    
                    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                        logger.info("✅ Medium-speed download successful!")
                        return file_path
                        
    except Exception as e:
        logger.warning(f"Medium-speed download failed: {e}")
    
    # Strategy 3: SAFE download (FALLBACK)
    try:
        await status_msg.edit_text("📥 Safe downloading...", parse_mode=None)
        logger.info("🔄 Attempting SAFE download")
        
        timeout = aiohttp.ClientTimeout(total=900, sock_read=240)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(download_url) as response:
                if response.status == 200:
                    async with aiofiles.open(file_path, 'wb') as file:
                        chunk_size = 1024 * 256  # 256KB chunks
                        async for chunk in response.content.iter_chunked(chunk_size):
                            await file.write(chunk)
                            await asyncio.sleep(0.01)  # Small delay
                    
                    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                        logger.info("✅ Safe download successful!")
                        return file_path
                        
    except Exception as e:
        logger.error(f"Safe download failed: {e}")
    
    # All strategies failed
    logger.error("❌ All download strategies failed")
    return None

# TeraboxDownloader class for backward compatibility
class TeraboxDownloader:
    """Compatibility class for existing handlers - FULLY ASYNC FIXED"""
    
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
        return await get_download_info(terabox_url, status_msg)
    
    async def download_with_resume(self, download_url: str, filename: str, status_msg, *args, **kwargs):
        """Download with resume - flexible parameter handling"""
        return await download_file(download_url, filename, status_msg)
    
    async def download_file(self, download_url: str, filename: str, status_msg, *args, **kwargs):
        """Download file method for handler compatibility"""
        return await download_file(download_url, filename, status_msg)
    
    async def cleanup_file(self, file_path: str):
        """Clean up downloaded file - NOW PROPERLY ASYNC (FIXES THE ERROR)"""
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
                                
