"""
Standard response messages
"""
import config

class StandardResponses:
    # Success responses
    DOWNLOAD_STARTED = f"{config.PROGRESS_PREFIX} Starting download..."
    UPLOAD_STARTED = f"{config.UPLOAD_PREFIX} Uploading to Telegram..."
    DOWNLOAD_COMPLETED = f"{config.SUCCESS_PREFIX} Download completed!"
    
    # Error responses
    INVALID_URL = f"{config.ERROR_PREFIX} Invalid Terabox URL"
    DOWNLOAD_FAILED = f"{config.ERROR_PREFIX} Download failed"
    UPLOAD_FAILED = f"{config.ERROR_PREFIX} Upload failed"
    VERIFICATION_FAILED = f"{config.ERROR_PREFIX} Verification failed"
    
    # Info responses
    BOT_STARTED = "🤖 Bot started successfully!"
    UNAUTHORIZED = "❌ You are not authorized to use this bot"
    OWNER_ONLY = "❌ This command is for bot owners only"
    
    # Verification responses
    VERIFICATION_REQUIRED = "🔐 Verification required to continue"
    VERIFICATION_SUCCESS = config.VERIFY_SUCCESS_MSG
    VERIFICATION_EXPIRED = config.VERIFY_EXPIRED_MSG
    
    # Queue responses
    DOWNLOAD_QUEUED = "📋 Download added to queue"
    QUEUE_FULL = "⏳ Queue is full, please try again later"
    ACTIVE_DOWNLOAD = "⏳ You already have an active download"
