#!/usr/bin/env python3
"""
Wrapper script to ensure proper import compatibility 
for Google Generative AI and other dependencies
"""
import sys
import os
import importlib

# Ensure our directory is in the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Try to establish compatibility for Google Generative AI imports
try:
    # First try to directly import the module
    import google.generativeai
    # Make it available as google.genai for compatibility
    sys.modules["google.genai"] = google.generativeai
    # Also try to make it available directly in the google namespace
    import google
    google.genai = google.generativeai
    print("Successfully set up google.genai compatibility layer")
except ImportError as e:
    print(f"Warning: Could not set up google.genai compatibility: {e}")
    try:
        # Try to install the package if it's missing
        import subprocess
        print("Attempting to install required Google packages...")
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "google-generativeai>=0.3.0,<0.4.0"
        ])
        # Try import again after installation
        import google.generativeai
        sys.modules["google.genai"] = google.generativeai
        import google
        google.genai = google.generativeai
        print("Successfully installed and set up google.genai compatibility")
    except Exception as e2:
        print(f"Error setting up Google Generative AI: {e2}")
        # Continue anyway, the main app will handle the error

# Now execute the main application
if __name__ == "__main__":
    print("Starting main application...")
    import main
    # If main has an app object (Flask app), run it
    if hasattr(main, 'app'):
        host = os.environ.get('HOST', '0.0.0.0')
        port = int(os.environ.get('PORT', 8080))
        debug = os.environ.get('DEBUG', 'False').lower() in ('true', '1', 't')
        main.app.run(host=host, port=port, debug=debug) 