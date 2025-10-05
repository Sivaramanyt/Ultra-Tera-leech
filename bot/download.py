"""
Download functionality - Stable Working Version (WDZone API + single-stream)
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
        """Create one shared HTTP session for API calls"""
        if not self.session or self.session.closed:
            connector = aiohttp.TCPConnector(
                limit=50,
                limit_per_host=5,
                ttl_dns_cache=300,
                use_dns_cache=True,
                keepalive_timeout=60,
                enable_cleanup_closed=True
            )
            timeout = aiohttp.ClientTimeout(total=300)  # 5 minutes for API
            self.session = aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                }
            )
        return self.session

    async def get_download_info(self, url: str, status_msg):
        """Use WDZone API to extract direct download URL"""
        try:
            await status_msg.edit_text(
                "📡 Getting download info...\n\n🔄 Server 1/1\n⚡ Please wait...",
                parse_mode="Markdown"
            )

            api = "https://wdzone-terabox-api.vercel.app/api"
            session = await self.get_session()
            async with session.get(api, params={"url": url}) as res:
                if res.status != 200:
                    return {"success": False, "error": f"API HTTP {res.status}"}
                data = await res.json()

            # WDZone keys have emojis; find them by name fragments
            status_key = next((k for k in data.keys() if "status" in k.lower()), None)
            info_key = next((k for k in data.keys() if "info" in k.lower()), None)
            if not status_key or data.get(status_key) != "Success" or not info_key:
                return {"success": False, "error": "API returned no success"}

            items = data.get(info_key) or []
            if not isinstance(items, list) or not items:
                return {"success": False, "error": "No items"}

            info = items[0]
            # Map fields with emoji names
            title = next((info[k] for k in info if "title" in k.lower() or "name" in k.lower()), "download")
            size = next((info[k] for k in info if "size" in k.lower()), "Unknown")
            download_url = next(
                (info[k] for k in info if "download" in k.lower() and isinstance(info[k], str) and info[k].startswith(("http://", "https://"))),
                None
            )
            if not download_url:
                return {"success": False, "error": "No download URL found"}

            logger.info(f"✅ Got download info: {title} ({size})")
            return {"success": True, "download_url": download_url, "filename": title, "size": size}

        except Exception as e:
            return {"success": False, "error": f"System error: {e}"}

    async def download_file(self, download_url: str, filename: str, status_msg):
        """
        Stable single-stream downloader:
        - follows redirects
        - large chunks
        - moderate progress updates
        """
        try:
            filename = self._sanitize_filename(filename)
            path = os.path.join(config.DOWNLOAD_DIR, filename)
            os.makedirs(config.DOWNLOAD_DIR, exist_ok=True)

            # Remove any previous partial file for clean behavior (old working flow)
            if os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass

            # Dedicated session for file transfer with generous timeouts
            connector = aiohttp.TCPConnector(
                limit=1,
                limit_per_host=1,
                keepalive_timeout=180,
                enable_cleanup_closed=True
            )
            timeout = aiohttp.ClientTimeout(
                total=1800,    # 30 min overall
                connect=30,    # connect fast
                sock_read=180  # 3 min between chunks
            )
            async with aiohttp.ClientSession(
                connector=connector,
                timeout=timeout,
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            ) as file_sess:

                async with file_sess.get(download_url, allow_redirects=True) as resp:
                    if resp.status != 200:
                        await status_msg.edit_text(
                            f"❌ Download failed\n\nHTTP {resp.status}\nPlease try again later!",
                            parse_mode="Markdown"
                        )
                        return None

                    total = int(resp.headers.get("content-length", 0))
                    downloaded = 0
                    last_update = 0
                    start = asyncio.get_event_loop().time()

                    chunk = 256 * 1024  # 256KB as in your working logs
                    async with aiofiles.open(path, "wb") as f:
                        async for part in resp.content.iter_chunked(chunk):
                            await f.write(part)
                            downloaded += len(part)

                            # update every 2 MB or on completion
                            if downloaded - last_update >= 2 * 1024 * 1024 or (total and downloaded >= total):
                                last_update = downloaded
                                if total:
                                    elapsed = max(0.001, asyncio.get_event_loop().time() - start)
                                    speed = downloaded / elapsed / (1024 * 1024)
                                    prog = downloaded / total * 100
                                    try:
                                        await status_msg.edit_text(
                                            f"📥 Downloading...\n\n"
                                            f"📊 Progress: {prog:.1f}%\n"
                                            f"💾 {self._fmt(downloaded)} / {self._fmt(total)}\n"
                                            f"⚡ {speed:.1f} MB/s",
                                            parse_mode="Markdown"
                                        )
                                    except Exception:
                                        pass

            # Verify size if available
            if total and os.path.getsize(path) < total * 0.95:
                await status_msg.edit_text(
                    "❌ File download failed\n\nPlease try again later!",
                    parse_mode="Markdown"
                )
                try:
                    os.remove(path)
                except Exception:
                    pass
                return None

            logger.info(f"✅ Download completed: {path}")
            return path

        except asyncio.TimeoutError:
            await status_msg.edit_text(
                "❌ Download timeout\n\nPlease try again later!",
                parse_mode="Markdown"
            )
            return None
        except Exception as e:
            logger.error(f"Download error: {e}")
            await status_msg.edit_text(
                "❌ File download failed\n\nPlease try again later!",
                parse_mode="Markdown"
            )
            return None

    def _sanitize_filename(self, filename: str) -> str:
        import re
        filename = re.sub(r'[<>:"/\\|?*]', "_", filename)
        if len(filename) > 200:
            name, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
            filename = name[:200 - len(ext) - 1] + ("." + ext if ext else "")
        return filename

    def _fmt(self, n: int) -> str:
        """Human readable bytes"""
        for unit in ("B", "KB", "MB", "GB"):
            if n < 1024:
                return f"{n:.1f} {unit}"
            n /= 1024.0
        return f"{n:.1f} TB"

    async def cleanup_file(self, file_path: str):
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass

    async def close(self):
        if self.session:
            await self.session.close()
            
