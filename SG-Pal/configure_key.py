#!/usr/bin/env python3
"""Run interactively on the Pi; never prints or bundles the secret."""
from getpass import getpass
from pathlib import Path
from core import atomic_json
path=Path.home()/'.config/sgpal/credentials.json'
print('Save your Common Ground API key privately to:',path)
if path.exists() and input('Replace the existing saved key? [y/N] ').lower()!='y': raise SystemExit('Unchanged.')
key=getpass('Paste API key (hidden), then Enter: ').strip()
if not key.startswith('sk-') or len(key)<20: raise SystemExit('That does not look like an OpenAI API key. Nothing saved.')
atomic_json(path,{'OPENAI_API_KEY':key})
path.chmod(0o600)
print('Key saved. No request was made. Start the app to test a photo.')
