#!/usr/bin/env python3
"""
Railway entry point that applies all compatibility patches
and makes the Flask app available for gunicorn
"""
import os
import sys

# Ensure our directory is in the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Apply all patches first
import wrapper  # This will apply all the compatibility patches

# Now import the Flask app from main
from main import app

if __name__ == "__main__":
    # If run directly, start the app
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False) 