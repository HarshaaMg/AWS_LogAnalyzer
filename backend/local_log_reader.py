import os
import re
from datetime import datetime
from typing import List, Dict
import json

class LocalLogReader:
    """Read and parse local log files"""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
    
    def read_log_file(self, filename: str) -> List[Dict]:
        """Read a log file and return parsed log entries"""
        filepath = os.path.join(self.log_dir, filename)
        if not os.path.exists(filepath):
            return []
        
        logs = []
        with open(filepath, 'r') as f:
            for line in f:
                log_entry = self._parse_log_line(line.strip())
                if log_entry:
                    logs.append(log_entry)
        
        return logs
    
    def _parse_log_line(self, line: str) -> Dict:
        """Parse a single log line"""
        if not line:
            return None
        
        # Try to match common log formats
        # Format: [TIMESTAMP] LEVEL MESSAGE
        pattern1 = r'\[(.*?)\]\s+(INFO|WARNING|ERROR|CRITICAL)\s+(.*)'
        match = re.match(pattern1, line)
        
        if match:
            timestamp_str, level, message = match.groups()
            try:
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S').isoformat()
            except:
                timestamp = datetime.now().isoformat()
            
            return {
                'log_id': f"log_{datetime.now().timestamp()}",
                'timestamp': timestamp,
                'level': level,
                'message': message,
                'severity': level,
                'source': 'local_file'
            }
        
        # Format: TIMESTAMP LEVEL MESSAGE
        pattern2 = r'(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\s+(INFO|WARNING|ERROR|CRITICAL)\s+(.*)'
        match = re.match(pattern2, line)
        
        if match:
            timestamp_str, level, message = match.groups()
            try:
                timestamp = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S').isoformat()
            except:
                timestamp = datetime.now().isoformat()
            
            return {
                'log_id': f"log_{datetime.now().timestamp()}",
                'timestamp': timestamp,
                'level': level,
                'message': message,
                'severity': level,
                'source': 'local_file'
            }
        
        # If no pattern matches, treat as INFO
        return {
            'log_id': f"log_{datetime.now().timestamp()}",
            'timestamp': datetime.now().isoformat(),
            'level': 'INFO',
            'message': line,
            'severity': 'INFO',
            'source': 'local_file'
        }
    
    def get_all_logs(self) -> List[Dict]:
        """Read all log files in the log directory"""
        all_logs = []
        for filename in os.listdir(self.log_dir):
            if filename.endswith('.log') or filename.endswith('.txt'):
                logs = self.read_log_file(filename)
                all_logs.extend(logs)
        
        # Sort by timestamp
        all_logs.sort(key=lambda x: x['timestamp'], reverse=True)
        return all_logs
    
    def filter_logs(self, logs: List[Dict], severity: str = None, limit: int = None) -> List[Dict]:
        """Filter logs by severity and limit"""
        filtered = logs
        
        if severity:
            filtered = [log for log in filtered if log['level'] == severity]
        
        if limit:
            filtered = filtered[:limit]
        
        return filtered
