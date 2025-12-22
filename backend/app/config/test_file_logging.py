"""
Test Script: Where Logs Are Stored

This script demonstrates where logs are stored with file logging enabled.

Usage:
    python -m app.config.test_file_logging
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.config import setup_logging, get_logger

# Test 1: Console only (default)
print("=" * 70)
print("TEST 1: Console Only Logging (Default)")
print("=" * 70)
print("Logs go to: Console/Terminal (stdout)")
print("Log file: None (not saved)")
print()

setup_logging()  # No log_file specified
logger = get_logger(__name__)
logger.info("This log goes to console only")
print()

# Test 2: With file logging
print("=" * 70)
print("TEST 2: File Logging Enabled")
print("=" * 70)

log_file = "logs/test_app.log"
print(f"Log file: {log_file}")
print(f"Full path: {Path(log_file).absolute()}")
print()

setup_logging(log_file=log_file)
logger = get_logger(__name__)
logger.info("This log goes to BOTH console AND file")
logger.warning("This warning is also saved to file")
logger.error("This error is saved to file")

print()
print("=" * 70)
print("✅ Check the log file:")
print(f"   {Path(log_file).absolute()}")
print()
print("View it with:")
print(f"   cat {log_file}")
print(f"   tail -f {log_file}")
print("=" * 70)

