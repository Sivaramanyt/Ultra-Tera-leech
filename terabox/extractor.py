"""
Terabox URL extraction and file info
"""
import re
import aiohttp
from loguru import logger
from typing import Dict, Optional

class TeraboxExtractor:
    def __init__(self):
        self.session = None
    
    async def extract_file_info(self, url: str) -> Optional[Dict]:
        """Extract file information from Terabox URL"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                    
                    # Extract filename from HTML
                    filename_match = re.search(r'"filename":"([^"]+)"', html)
                    if filename_match:
                        filename = filename_match.group(1)
                    else:
                        # Fallback filename extraction
                        filename_match = re.search(r'<title>([^<]+)</title>', html)
                        filename = filename_match.group(1) if filename_match else "download"
                    
                    # Extract file size
                    size_match = re.search(r'"size":(\d+)', html)
                    size = int(size_match.group(1)) if size_match else 0
                    
                    # Extract file ID
                    file_id_match = re.search(r'"fsid":(\d+)', html)
                    file_id = file_id_match.group(1) if file_id_match else None
                    
                    return {
                        'filename': filename,
                        'size': size,
                        'file_id': file_id,
                        'url': url
                    }
                    
        except Exception as e:
            logger.error(f"Extraction error: {e}")
        
        return None
    
    async def extract_direct_url(self, url: str) -> Optional[str]:
        """Extract direct download URL"""
        try:
            # This is a simplified version - real implementation would be more complex
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www.terabox.com/'
            }
            
            async with self.session.get(url, headers=headers) as response:
                if response.status == 200:
                    html = await response.text()
                    
                    # Look for direct download patterns
                    patterns = [
                        r'"dlink":"([^"]+)"',
                        r'"download_url":"([^"]+)"',
                        r'downloadUrl":"([^"]+)"'
                    ]
                    
                    for pattern in patterns:
                        match = re.search(pattern, html)
                        if match:
                            return match.group(1).replace('\\/', '/')
                            
        except Exception as e:
            logger.error(f"Direct extraction error: {e}")
        
        return None
    
    async def cleanup(self):
        """Cleanup session"""
        if self.session:
            await self.session.close()
