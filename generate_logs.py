#!/usr/bin/env python3
"""
Script to generate dummy log files for local testing
"""
import sys
import os

# Add backend directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from dummy_log_generator import DummyLogGenerator

def main():
    print("Generating dummy log files...")
    
    # Create generator instance
    generator = DummyLogGenerator(log_dir='backend/logs')
    
    # Generate 200 dummy logs
    print("Generating 200 dummy log entries...")
    generator.generate_logs(count=200, filename='application.log')
    
    # Generate some additional log files for variety
    print("Generating additional log files...")
    generator.generate_logs(count=50, filename='system.log')
    generator.generate_logs(count=30, filename='auth.log')
    
    print("\n✓ Dummy log files generated successfully!")
    print("  - backend/logs/application.log (200 entries)")
    print("  - backend/logs/system.log (50 entries)")
    print("  - backend/logs/auth.log (30 entries)")
    print("\nYou can now start the application with: docker-compose up -d")

if __name__ == "__main__":
    main()
