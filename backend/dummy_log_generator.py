import os
import random
from datetime import datetime, timedelta
from typing import List

class DummyLogGenerator:
    """Generate dummy log files for testing"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
    
    def generate_logs(self, count: int = 100, filename: str = "application.log"):
        """Generate dummy log entries"""
        log_levels = ['INFO', 'WARNING', 'ERROR', 'CRITICAL']
        
        # Sample log messages for each level
        info_messages = [
            "Application started successfully",
            "User login successful",
            "Database connection established",
            "Cache refreshed",
            "Request processed successfully",
            "Background job completed",
            "Configuration loaded",
            "Service health check passed",
            "Data synchronization completed",
            "API request received"
        ]
        
        warning_messages = [
            "High memory usage detected",
            "Slow database query detected",
            "Disk space running low",
            "Rate limit approaching",
            "Deprecated API endpoint used",
            "Large payload size warning",
            "Connection pool nearly exhausted",
            "Cache miss rate increasing",
            "Response time above threshold",
            "Retry attempt initiated"
        ]
        
        error_messages = [
            "Database connection failed",
            "API request timeout",
            "Authentication failed",
            "Invalid user input",
            "File not found",
            "Network unreachable",
            "Service unavailable",
            "Data validation error",
            "Permission denied",
            "Resource not found"
        ]
        
        critical_messages = [
            "System crash imminent",
            "Database corruption detected",
            "Security breach attempt",
            "Out of memory error",
            "Complete service failure",
            "Data loss detected",
            "Critical system component failed",
            "Emergency shutdown initiated",
            "Fatal error in core module",
            "Unrecoverable system state"
        ]
        
        logs = []
        base_time = datetime.now() - timedelta(hours=1)
        
        for i in range(count):
            # Randomly select log level with weighted distribution
            level = random.choices(
                log_levels,
                weights=[0.6, 0.2, 0.15, 0.05],  # More INFO, fewer CRITICAL
                k=1
            )[0]
            
            # Select message based on level
            if level == 'INFO':
                message = random.choice(info_messages)
            elif level == 'WARNING':
                message = random.choice(warning_messages)
            elif level == 'ERROR':
                message = random.choice(error_messages)
            else:  # CRITICAL
                message = random.choice(critical_messages)
            
            # Generate timestamp with some randomness
            timestamp = base_time + timedelta(
                seconds=random.randint(0, 3600),
                milliseconds=random.randint(0, 999)
            )
            
            log_entry = f"[{timestamp.strftime('%Y-%m-%d %H:%M:%S')}] {level} {message}"
            logs.append(log_entry)
        
        # Sort logs by timestamp
        logs.sort()
        
        # Write to file
        filepath = os.path.join(self.log_dir, filename)
        with open(filepath, 'w') as f:
            f.write('\n'.join(logs))
        
        print(f"Generated {count} dummy logs in {filepath}")
        return logs
    
    def generate_streaming_logs(self, interval: int = 5, filename: str = "application.log"):
        """Generate logs continuously (for testing streaming)"""
        import time
        
        log_levels = ['INFO', 'WARNING', 'ERROR', 'CRITICAL']
        messages = [
            "Processing request",
            "User action logged",
            "Database query executed",
            "Cache updated",
            "Error occurred in module",
            "Warning: high latency",
            "Critical: system overload"
        ]
        
        filepath = os.path.join(self.log_dir, filename)
        
        print(f"Streaming logs to {filepath} every {interval} seconds. Press Ctrl+C to stop.")
        
        try:
            while True:
                level = random.choice(log_levels)
                message = random.choice(messages)
                timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                
                log_entry = f"[{timestamp}] {level} {message}\n"
                
                with open(filepath, 'a') as f:
                    f.write(log_entry)
                
                print(f"Added: {log_entry.strip()}")
                time.sleep(interval)
        except KeyboardInterrupt:
            print("\nStreaming stopped.")

if __name__ == "__main__":
    generator = DummyLogGenerator()
    
    # Generate 100 dummy logs
    generator.generate_logs(100)
    
    # Uncomment below for streaming logs
    # generator.generate_streaming_logs(interval=5)
