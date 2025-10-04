import os
import sys
import threading
import socket

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

if __name__ == "__main__":
    os.makedirs(config.DOWNLOAD_DIR, exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    threading.Thread(target=health, daemon=True).start()
    TeraboxBot().run()
    
