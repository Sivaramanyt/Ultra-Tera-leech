"""
Shortlink generation with multiple APIs
"""
import aiohttp
from loguru import logger
from typing import Optional
from urllib.parse import quote
import config

class ShortlinkGenerator:
    def __init__(self):
        self.session = None
    
    async def create_shortlink(self, url: str) -> Optional[str]:
        """Create shortlink using configured API"""
        try:
            if not config.SHORTLINK_API or not config.SHORTLINK_URL:
                return url  # Return original if no API configured
            
            if not self.session:
                self.session = aiohttp.ClientSession()
            
            shortlink_type = config.SHORTLINK_TYPE.lower()
            
            if shortlink_type == 'shorte.st':
                return await self._shorte_st(url)
            elif shortlink_type == 'droplink':
                return await self._droplink(url)
            elif shortlink_type == 'clk.sh':
                return await self._clksh(url)
            else:
                return await self._generic(url)
                
        except Exception as e:
            logger.error(f"Shortlink creation error: {e}")
            return url  # Return original URL if shortlink fails
    
    async def _shorte_st(self, url: str) -> Optional[str]:
        """Shorte.st API"""
        try:
            api_url = "https://api.shorte.st/v1/data/url"
            headers = {"public-api-token": config.SHORTLINK_API}
            data = {"urlToShorten": url}
            
            async with self.session.post(api_url, headers=headers, data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get('shortenedUrl')
        except Exception as e:
            logger.error(f"Shorte.st error: {e}")
        return None
    
    async def _droplink(self, url: str) -> Optional[str]:
        """Droplink API"""
        try:
            api_url = f"https://droplink.co/api"
            params = {
                "api": config.SHORTLINK_API,
                "url": url,
                "format": "json"
            }
            
            async with self.session.get(api_url, params=params) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get('shortenedUrl')
        except Exception as e:
            logger.error(f"Droplink error: {e}")
        return None
    
    async def _clksh(self, url: str) -> Optional[str]:
        """Clk.sh API"""
        try:
            api_url = "https://clk.sh/api"
            data = {
                "api": config.SHORTLINK_API,
                "url": url
            }
            
            async with self.session.post(api_url, data=data) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get('shortenedUrl')
        except Exception as e:
            logger.error(f"Clk.sh error: {e}")
        return None
    
    async def _generic(self, url: str) -> Optional[str]:
        """Generic shortlink API"""
        try:
            # Generic format - adjust based on your API
            api_url = f"{config.SHORTLINK_URL}/api"
            data = {
                "api": config.SHORTLINK_API,
                "url": url
            }
            
            async with self.session.post(api_url, json=data) as response:
                if response.status == 200:
                    result = await response.json()
                    # Try different response fields
                    for field in ['short_url', 'shortenedUrl', 'url', 'link']:
                        if field in result:
                            return result[field]
        except Exception as e:
            logger.error(f"Generic shortlink error: {e}")
        return None
    
    async def cleanup(self):
        """Cleanup session"""
        if self.session:
            await self.session.close()
