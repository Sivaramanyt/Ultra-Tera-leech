import os
import sys
import threading
import socket
import time

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from bot.core import TeraboxBot
import config

def health():
    s = socket.socket()
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(('0.0.0.0', 8000))
    s.listen(1)
    while True:
        c, a = s.accept()
        c.send(b"HTTP/1.1 200 OK\r\n\r\nOK")
        c.close()

def start_bot_safely():
    """Start bot with conflict protection"""
    max_retries = 3
    retry_delay = 10
    
    for attempt in range(max_retries):
        try:
            print(f"🚀 Starting bot (attempt {attempt + 1}/{max_retries})...")
            bot = TeraboxBot()
            bot.run()
            break  # If successful, exit loop
        except Exception as e:
            if "Conflict" in str(e):
                print(f"⚠️  Conflict detected on attempt {attempt + 1}")
                if attempt < max_retries - 1:
                    print(f"⏳ Waiting {retry_delay} seconds before retry...")
                    time.sleep(retry_delay)
                    retry_delay += 5  # Increase delay each retry
                else:
                    print("❌ Max retries reached. Bot may already be running elsewhere.")
            else:
                print(f"❌ Unexpected error: {e}")
                raise

if __name__ == "__main__":
    os.makedirs(config.DOWNLOAD_DIR, exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # Start health server
    threading.Thread(target=health, daemon=True).start()
    
    # Start bot with retry logic
    start_bot_safely()
                
