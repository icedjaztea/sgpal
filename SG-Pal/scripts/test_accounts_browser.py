"""Compatibility command: current account UI uses real recovery codes.
Legacy email provider contracts remain covered in tests/test_accounts.py.
"""
from pathlib import Path
import runpy
runpy.run_path(str(Path(__file__).with_name('test_recovery_browser.py')),run_name='__main__')
