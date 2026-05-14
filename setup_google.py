#!/usr/bin/env python3
"""
Run this once to complete Google OAuth and store your token.
Usage: python setup_google.py
"""
from integrations.auth import get_google_credentials

if __name__ == "__main__":
    creds = get_google_credentials()
    print("Google authentication successful.")
    print(f"Token written to: token.json")
