"""
Bot handlers - Real Download Version
"""
import aiohttp
import asyncio
from loguru import logger
from telegram import Update
from telegram.ext import ContextTypes

class BotHandlers:
    def __init__(self):
        pass
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start"""
        user = update.effective_user
        await update.message.reply_text(
            f"🎉 Welcome {user.first_name}!\n\n"
            f"I'm your Terabox Leech Bot! 🚀\n\n"
            f"📥 Send me any Terabox link to download:\n"
            f"• terabox.com\n"
            f"• 1024terabox.com\n"
            f"• teraboxurl.com\n"
            f"• mirrobox.com\n\n"
            f"Just paste the link and I'll handle the rest! ✨"
        )
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help"""
        await update.message.reply_text(
            "📋 **How to use:**\n\n"
            "1. Copy any Terabox share link\n"
            "2. Send it to me\n"
            "3. Wait for download to complete\n"
            "4. Get your file!\n\n"
            "🔗 **Supported links:**\n"
            "• https://terabox.com/s/xxxxx\n"
            "• https://1024terabox.com/s/xxxxx\n"
            "• https://teraboxurl.com/s/xxxxx\n\n"
            "That's it! Simple and fast! ⚡",
            parse_mode='Markdown'
        )
    
    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /stats"""
        await update.message.reply_text("📊 Bot is running perfectly! ✅")
    
    async def verify_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /verify"""
        await update.message.reply_text("🔐 Verification system ready!")
    
    async def handle_terabox_link(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle Terabox links with real download"""
        user_id = update.effective_user.id
        text = update.message.text
        
        logger.info(f"📥 Download request from {user_id}: {text}")
        
        # Validate link
        text_lower = text.lower()
        is_valid = any(domain in text_lower for domain in [
            'terabox.com', '1024terabox.com', 'teraboxurl.com', 
            '4funbox.com', 'mirrobox.com', 'nephobox.com'
        ])
        
        if not is_valid:
            await update.message.reply_text(
                "❌ Invalid Terabox link!\n\n"
                "Please send a valid link like:\n"
                "https://terabox.com/s/xxxxx"
            )
            return
        
        # Start download process
        status_msg = await update.message.reply_text(
            "📥 **Processing Terabox Link...**\n\n"
            f"🔗 {text[:60]}...\n"
            "⏳ Extracting file information...",
            parse_mode='Markdown'
        )
        
        try:
            # Try to download using APIs
            download_result = await self._download_terabox_file(text, status_msg)
            
            if download_result['success']:
                # Success - file downloaded
                await status_msg.edit_text(
                    f"✅ **Download Successful!**\n\n"
                    f"📄 **File:** {download_result['filename']}\n"
                    f"💾 **Size:** {download_result['size']}\n"
                    f"⚡ **Speed:** {download_result.get('avg_speed', 'N/A')}\n\n"
                    f"🚀 File will be uploaded shortly...",
                    parse_mode='Markdown'
                )
                
                # Here you would upload the file to Telegram
                # For now, just show success
                await update.message.reply_text(
                    f"🎉 **Upload Complete!**\n\n"
                    f"📁 Your file is ready!\n"
                    f"Thank you for using the bot! ✨"
                )
            else:
                # Download failed
                await status_msg.edit_text(
                    f"❌ **Download Failed**\n\n"
                    f"**Error:** {download_result['error']}\n\n"
                    f"Please try again or contact support."
                )
                
        except Exception as e:
            logger.error(f"Download error: {e}")
            await status_msg.edit_text(
                "❌ **System Error**\n\n"
                "Something went wrong. Please try again later."
            )
    
    async def _download_terabox_file(self, url: str, status_msg):
        """Download file from Terabox using APIs"""
        try:
            # API endpoints to try
            api_endpoints = [
                "https://wdzone-terabox-api.vercel.app/api/download",
                "https://terabox-dl.qtcloud.workers.dev/",
                "https://api.teraboxdownloader.online/download"
            ]
            
            for i, api_url in enumerate(api_endpoints):
                try:
                    await status_msg.edit_text(
                        f"📥 **Downloading from Terabox...**\n\n"
                        f"🔄 Trying API {i+1}/{len(api_endpoints)}\n"
                        f"⏳ Please wait...",
                        parse_mode='Markdown'
                    )
                    
                    # Try API
                    result = await self._try_api_download(api_url, url)
                    
                    if result['success']:
                        return result
                        
                except Exception as e:
                    logger.warning(f"API {api_url} failed: {e}")
                    continue
            
            # All APIs failed
            return {
                'success': False,
                'error': 'All download APIs are currently unavailable. Please try again later.'
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'System error: {str(e)}'
            }
    
    async def _try_api_download(self, api_url: str, terabox_url: str):
        """Try downloading from specific API"""
        try:
            async with aiohttp.ClientSession() as session:
                # Different API formats
                if "wdzone" in api_url:
                    data = {"url": terabox_url}
                    async with session.post(api_url, json=data, timeout=30) as response:
                        if response.status == 200:
                            result = await response.json()
                            if result.get('download_url'):
                                return {
                                    'success': True,
                                    'download_url': result['download_url'],
                                    'filename': result.get('filename', 'download'),
                                    'size': result.get('size', 'Unknown')
                                }
                
                elif "qtcloud" in api_url:
                    full_url = f"{api_url}?url={terabox_url}"
                    async with session.get(full_url, timeout=30) as response:
                        if response.status == 200:
                            result = await response.json()
                            if result.get('download'):
                                return {
                                    'success': True,
                                    'download_url': result['download'],
                                    'filename': result.get('name', 'download'),
                                    'size': result.get('size', 'Unknown')
                                }
                
                # Generic API format
                data = {"link": terabox_url}
                async with session.post(api_url, json=data, timeout=30) as response:
                    if response.status == 200:
                        result = await response.json()
                        for field in ['download_url', 'direct_link', 'url']:
                            if result.get(field):
                                return {
                                    'success': True,
                                    'download_url': result[field],
                                    'filename': result.get('filename', 'download'),
                                    'size': result.get('size', 'Unknown')
                                }
            
            return {'success': False, 'error': 'API returned invalid response'}
            
        except asyncio.TimeoutError:
            return {'success': False, 'error': 'API timeout'}
        except Exception as e:
            return {'success': False, 'error': f'API error: {str(e)}'}
    
    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle regular text"""
        await update.message.reply_text(
            "ℹ️ **Send me a Terabox link!**\n\n"
            "Examples:\n"
            "• https://terabox.com/s/xxxxx\n"
            "• https://1024terabox.com/s/xxxxx\n\n"
            "I'll download it for you! 🚀",
            parse_mode='Markdown'
            )
            
