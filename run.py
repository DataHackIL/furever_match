#!/usr/bin/env python
"""
Simple script to run the FureverMatch Flask app
Supports easy startup and shutdown with Ctrl+C
"""
import sys
import os
import signal

# Add the project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def signal_handler(sig, frame):
    """Handle graceful shutdown on Ctrl+C"""
    print("\n\n🛑 Shutting down FureverMatch App...")
    sys.exit(0)


if __name__ == "__main__":
    # Register signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)

    print("🚀 Starting FureverMatch App...")
    print("📍 Open browser to: http://localhost:8000")
    print("⏹️  Press Ctrl+C to stop\n")

    from furever_match.main import main
    main()
