"""
Download functionality - Minimal Working Version
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
        if not self.session or self.session.closed:
            self.session = aiohttp.ClientSession()
        return self.session
    
    async def get_download_info(self, url: str, status_msg):
        try:
            session = await self.get_session()
            api_url = 'https://wdzone-terabox-api.vercel.app/api'
            
            async with session.get(api_url, params={'url': url}) as response:
                if response.status == 200:
                    result = await response.json()
                    
                    # Find keys with emojis
                    status_key = next((k for k in result.keys() if 'Status' in k), None)
                    info_key = next((k for k in result.keys() if 'Info' in k), None)
                    
                    if status_key and info_key and result.get(status_key) == 'Success':
                        info = result.get(info_key)[0]
                        
                        # Extract info
                        download_url = next((v for k, v in info.items() if 'Download' in k and v.startswith('https://')), None)
                        filename = next((v for k, v in info.items() if 'Title' in k), 'download.mp4')
                        size = next((v for k, v in info.items() if 'Size' in k), 'Unknown')
                        
                        if download_url:
                            return {'success': True, 'download_url': download_url, 'filename': filename, 'size': size}
            
            return {'success': False, 'error': 'No download URL'}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    async def download_file(self, download_url: str, filename: str, status_msg):
        try:
            file_path = os.path.join(config.DOWNLOAD_DIR, filename)
            os.makedirs(config.DOWNLOAD_DIR, exist_ok=True)
            
            session = await self.get_session()
            
            async with session.get(download_url) as response:
                if response.status == 200:
                    async with aiofiles.open(file_path, 'wb') as file:
                        async for chunk in response.content.iter_chunked(8192):
                            await file.write(chunk)
                    
                    return file_path if os.path.exists(file_path) else None
            return None
            
        except Exception as e:
            logger.error(f"Download error: {e}")
            return None
    
    async def cleanup_file(self, file_path: str):
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except:
            pass
    
    async def close(self):
        if self.session:
            await self.session.close()
                        
