"""
Main Terabox downloader with multiple API fallbacks
"""
import os
import asyncio
import aiofiles
import aiohttp
from loguru import logger
from typing import Dict, Optional, Callable

from .api import TeraboxAPI
from .extractor import TeraboxExtractor
from utils.helpers import format_bytes, calculate_eta
import config

class TeraboxDownloader:
    def __init__(self):
        self.api = TeraboxAPI()
        self.extractor = TeraboxExtractor()
        self.session = None
    
    async def download_file(self, url: str, progress_callback: Optional[Callable] = None) -> Dict:
        """
        Download file with hybrid approach
        Returns: {'success': bool, 'file_path': str, 'filename': str, 'size': str, 'error': str}
        """
        try:
            logger.info(f"Starting download: {url}")
            
            # Step 1: Get file info
            file_info = await self.extractor.extract_file_info(url)
            if not file_info:
                return {'success': False, 'error': 'Failed to extract file info'}
            
            # Step 2: Get download URL
            download_url = await self._get_download_url(url, file_info)
            if not download_url:
                return {'success': False, 'error': 'Failed to get download URL'}
            
            # Step 3: Download with progress
            result = await self._download_with_progress(download_url, file_info, progress_callback)
            return result
            
        except Exception as e:
            logger.error(f"Download error: {e}")
            return {'success': False, 'error': f'Download failed: {str(e)}'}
    
    async def _get_download_url(self, original_url: str, file_info: Dict) -> Optional[str]:
        """Get download URL using multiple methods"""
        
        # Method 1: Third-party APIs
        logger.info("Trying APIs...")
        for endpoint in config.TERABOX_API_ENDPOINTS:
            try:
                download_url = await self.api.get_download_url(original_url, endpoint)
                if download_url:
                    logger.info(f"Success with: {endpoint}")
                    return download_url
            except Exception as e:
                logger.warning(f"API failed {endpoint}: {e}")
                continue
        
        # Method 2: Direct extraction
        logger.info("Trying direct extraction...")
        try:
            download_url = await self.extractor.extract_direct_url(original_url)
            if download_url:
                return download_url
        except Exception as e:
            logger.warning(f"Direct extraction failed: {e}")
        
        return None
    
    async def _download_with_progress(self, download_url: str, file_info: Dict, progress_callback: Optional[Callable]) -> Dict:
        """Download with progress tracking"""
        
        filename = file_info.get('filename', 'download')
        file_path = os.path.join(config.DOWNLOAD_DIR, filename)
        
        # Ensure unique filename
        counter = 1
        base_name, ext = os.path.splitext(filename)
        while os.path.exists(file_path):
            filename = f"{base_name}_{counter}{ext}"
            file_path = os.path.join(config.DOWNLOAD_DIR, filename)
            counter += 1
        
        try:
            if not self.session:
                self.session = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=300))
            
            async with self.session.get(download_url) as response:
                if response.status != 200:
                    return {'success': False, 'error': f'HTTP {response.status}'}
                
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                start_time = asyncio.get_event_loop().time()
                
                async with aiofiles.open(file_path, 'wb') as file:
                    async for chunk in response.content.iter_chunked(8192):
                        await file.write(chunk)
                        downloaded += len(chunk)
                        
                        if progress_callback and total_size > 0:
                            current_time = asyncio.get_event_loop().time()
                            elapsed = current_time - start_time
                            
                            if elapsed > 0:
                                speed = downloaded / elapsed
                                eta = calculate_eta(downloaded, total_size, speed)
                                speed_str = f"{format_bytes(speed)}/s"
                                
                                await progress_callback(downloaded, total_size, speed_str, eta)
                
                return {
                    'success': True,
                    'file_path': file_path,
                    'filename': filename,
                    'size': format_bytes(downloaded)
                }
                
        except Exception as e:
            if os.path.exists(file_path):
                os.remove(file_path)
            return {'success': False, 'error': f'Download failed: {str(e)}'}
    
    async def cleanup(self):
        """Cleanup resources"""
        if self.session:
            await self.session.close()
