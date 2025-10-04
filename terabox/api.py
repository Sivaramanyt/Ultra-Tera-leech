"""
Terabox API integrations
"""
import aiohttp
from loguru import logger
from typing import Optional

class TeraboxAPI:
    def __init__(self):
        self.session = None
    
    async def get_download_url(self, terabox_url: str, api_endpoint: str) -> Optional[str]:
        """Get download URL from API endpoint"""
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            # Different API formats
            if "wdzone" in api_endpoint:
                return await self._wdzone_api(terabox_url, api_endpoint)
            elif "teradownloader" in api_endpoint:
                return await self._teradownloader_api(terabox_url, api_endpoint)
            elif "qtcloud" in api_endpoint:
                return await self._qtcloud_api(terabox_url, api_endpoint)
            else:
                return await self._generic_api(terabox_url, api_endpoint)
                
        except Exception as e:
            logger.error(f"API error: {e}")
            return None
    
    async def _wdzone_api(self, url: str, endpoint: str) -> Optional[str]:
        """WDZone API format"""
        try:
            data = {"url": url}
            async with self.session.post(endpoint, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get('download_url') or result.get('downloadUrl')
        except Exception as e:
            logger.error(f"WDZone API error: {e}")
        return None
    
    async def _teradownloader_api(self, url: str, endpoint: str) -> Optional[str]:
        """TeraDownloader API format"""
        try:
            params = {"url": url}
            async with self.session.get(endpoint, params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get('download_link') or result.get('direct_link')
        except Exception as e:
            logger.error(f"TeraDownloader API error: {e}")
        return None
    
    async def _qtcloud_api(self, url: str, endpoint: str) -> Optional[str]:
        """QTCloud Workers API format"""
        try:
            full_url = f"{endpoint}?url={url}"
            async with self.session.get(full_url) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get('download') or result.get('url')
        except Exception as e:
            logger.error(f"QTCloud API error: {e}")
        return None
    
    async def _generic_api(self, url: str, endpoint: str) -> Optional[str]:
        """Generic API format"""
        try:
            data = {"link": url, "url": url}
            async with self.session.post(endpoint, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    # Try common response fields
                    for field in ['download_url', 'downloadUrl', 'direct_link', 'url', 'link']:
                        if field in result:
                            return result[field]
        except Exception as e:
            logger.error(f"Generic API error: {e}")
        return None
    
    async def cleanup(self):
        """Cleanup session"""
        if self.session:
            await self.session.close()
