"""
Simple but Reliable Download Module
"""
import os
import asyncio
import aiohttp
import aiofiles
from loguru import logger
import config

async def get_download_info(terabox_url: str):
    """Get download information from API"""
    api_url = f"https://wdzone-terabox-api.vercel.app/file_info?url={terabox_url}"
    
    timeout = aiohttp.ClientTimeout(total=30)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.get(api_url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    if data.get("ok") and data.get("file_info"):
                        file_info = data["file_info"]
                        file_name = file_info.get("file_name", "unknown_file")
                        file_size = file_info.get("size", 0)
                        download_url = file_info.get("download_url")
                        
                        if download_url:
                            # Convert size to MB for logging
                            size_mb = file_size / (1024 * 1024) if file_size else 0
                            logger.info(f"✅ WDZone API Success - File: {file_name}, Size: {size_mb:.2f} MB")
                            
                            return {
                                "file_name": file_name,
                                "file_size": file_size, 
                                "download_url": download_url
                            }
                    
                    logger.error(f"❌ API returned invalid data: {data}")
                    raise Exception("Invalid API response")
                else:
                    logger.error(f"❌ API request failed with status {response.status}")
                    raise Exception(f"API request failed: {response.status}")
        except Exception as e:
            logger.error(f"❌ API request error: {e}")
            raise

def _sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    import re
    # Remove invalid characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
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
    
    # Strategy 1: Large chunks (fast)
    try:
        await status_msg.edit_text("📥 Downloading with large chunks...", parse_mode=None)
        logger.info("🔄 Attempting large chunk download")
        
        timeout = aiohttp.ClientTimeout(total=300, sock_read=60)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(download_url) as response:
                if response.status == 200:
                    async with aiofiles.open(file_path, 'wb') as file:
                        chunk_size = 1024 * 512  # 512KB chunks
                        async for chunk in response.content.iter_chunked(chunk_size):
                            await file.write(chunk)
                    
                    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                        logger.info("✅ Large chunk download successful!")
                        return file_path
    except Exception as e:
        logger.warning(f"Large chunk download failed: {e}")
    
    # Strategy 2: Medium chunks
    try:
        await status_msg.edit_text("📥 Retrying with medium chunks...", parse_mode=None)
        logger.info("🔄 Attempting medium chunk download")
        
        timeout = aiohttp.ClientTimeout(total=300, sock_read=30)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(download_url) as response:
                if response.status == 200:
                    async with aiofiles.open(file_path, 'wb') as file:
                        chunk_size = 1024 * 64  # 64KB chunks
                        async for chunk in response.content.iter_chunked(chunk_size):
                            await file.write(chunk)
                            await asyncio.sleep(0.01)  # Small delay
                    
                    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                        logger.info("✅ Medium chunk download successful!")
                        return file_path
    except Exception as e:
        logger.warning(f"Medium chunk download failed: {e}")
    
    # Strategy 3: Small chunks (most reliable)
    try:
        await status_msg.edit_text("📥 Final retry with small chunks...", parse_mode=None)
        logger.info("🔄 Attempting small chunk download")
        
        timeout = aiohttp.ClientTimeout(total=600, sock_read=120)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(download_url) as response:
                if response.status == 200:
                    async with aiofiles.open(file_path, 'wb') as file:
                        chunk_size = 1024 * 4  # 4KB chunks
                        async for chunk in response.content.iter_chunked(chunk_size):
                            await file.write(chunk)
                            await asyncio.sleep(0.05)  # Longer delay for stability
                    
                    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                        logger.info("✅ Small chunk download successful!")
                        return file_path
    except Exception as e:
        logger.error(f"Small chunk download failed: {e}")
    
    # All strategies failed
    logger.error("❌ All download strategies failed")
    return None
    
