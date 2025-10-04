"""
Progress tracking utilities
"""
import time
from typing import Optional

class ProgressTracker:
    def __init__(self):
        self.start_time = None
        self.last_update = 0
    
    def start(self):
        """Start progress tracking"""
        self.start_time = time.time()
        self.last_update = self.start_time
    
    def should_update(self, interval: int = 2) -> bool:
        """Check if progress should be updated"""
        current_time = time.time()
        if current_time - self.last_update >= interval:
            self.last_update = current_time
            return True
        return False
    
    def get_speed(self, downloaded: int) -> float:
        """Calculate current speed"""
        if not self.start_time:
            return 0
        
        elapsed = time.time() - self.start_time
        return downloaded / elapsed if elapsed > 0 else 0
    
    def create_progress_bar(self, percentage: float, length: int = 10) -> str:
        """Create ASCII progress bar"""
        filled = int(percentage / 100 * length)
        bar = "█" * filled + "░" * (length - filled)
        return f"[{bar}]"
