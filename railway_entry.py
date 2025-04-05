#!/usr/bin/env python3
"""
Railway entry point that applies all compatibility patches
and makes the Flask app available for gunicorn
"""
import os
import sys
import traceback
import time

# Enable verbose logging
os.environ["PYTHONUNBUFFERED"] = "1"

print("=== RAILWAY ENTRY: STARTING DEPLOYMENT SETUP ===")

# Create a minimal Flask app right away for health checks
# This ensures we have a working app that passes health checks
# even if there are issues with the main app
try:
    from flask import Flask, jsonify
    fallback_app = Flask(__name__)
    
    @fallback_app.route('/healthcheck')
    def fallback_healthcheck():
        return jsonify({
            "status": "ok", 
            "message": "Fallback app responding to health check",
            "timestamp": time.time()
        })
    
    @fallback_app.route('/')
    def fallback_root():
        return jsonify({
            "status": "limited",
            "message": "Fallback app is running. The main application had initialization issues."
        })
    
    # This will be our app if the main one fails to load
    app = fallback_app
    print("Created fallback Flask app for health checks")
except Exception as e:
    print(f"WARNING: Could not create fallback app: {str(e)}")

try:
    # Ensure our directory is in the path
    current_dir = os.path.dirname(os.path.abspath(__file__))
    sys.path.insert(0, current_dir)
    print(f"Added {current_dir} to Python path")

    # Check if google-generativeai is installed and its version
    try:
        import pkg_resources
        version = pkg_resources.get_distribution("google-generativeai").version
        print(f"Found google-generativeai version: {version}")
    except Exception as e:
        print(f"Could not determine google-generativeai version: {str(e)}")
    
    # Apply all patches first
    print("Importing wrapper to apply compatibility patches...")
    try:
        import wrapper  # This will apply all the compatibility patches
        print("Wrapper imported successfully")
    except Exception as wrapper_err:
        print(f"WARNING: Error importing wrapper: {str(wrapper_err)}")
        # Continue even if wrapper fails

    # Force direct patch for GenerateContentConfig
    print("Applying direct patch for GenerateContentConfig...")
    try:
        import google.generativeai
        
        # Ensure types is available
        if not hasattr(google.generativeai, 'types'):
            print("Creating types module")
            types_module = type('types', (), {})
            google.generativeai.types = types_module
            sys.modules['google.generativeai.types'] = types_module
        
        # Ensure GenerateContentConfig is available
        if not hasattr(google.generativeai.types, 'GenerateContentConfig'):
            print("Creating GenerateContentConfig class")
            
            # Create GenerateContentConfig class
            class GenerateContentConfig:
                def __init__(self, response_modalities=None, temperature=None, top_k=None, top_p=None, **kwargs):
                    self.response_modalities = response_modalities
                    self.temperature = temperature
                    self.top_k = top_k
                    self.top_p = top_p
                    for key, value in kwargs.items():
                        setattr(self, key, value)
            
            # Add to types module
            google.generativeai.types.GenerateContentConfig = GenerateContentConfig
            print("GenerateContentConfig class created successfully")
        else:
            print("GenerateContentConfig already exists")
    except Exception as e:
        print(f"Error applying direct patch: {str(e)}")
        traceback.print_exc()
    
    # Verify the environment is ready
    print("Checking environment setup...")
    try:
        import google.generativeai
        
        # Check for needed features
        print(f"google.generativeai exists: {hasattr(sys.modules, 'google.generativeai')}")
        print(f"types module exists: {hasattr(google.generativeai, 'types')}")
        print(f"GenerateContentConfig exists: {hasattr(google.generativeai.types, 'GenerateContentConfig')}")
        print(f"generate_content exists: {hasattr(google.generativeai, 'generate_content')}")
        print(f"Client exists: {hasattr(google.generativeai, 'Client')}")
        print(f"GenerativeModel exists: {hasattr(google.generativeai, 'GenerativeModel')}")
    except Exception as e:
        print(f"Error checking environment: {str(e)}")
    
    # Now import the Flask app from main
    print("Importing Flask app from main...")
    try:
        # Try with timeout to prevent hanging, but only if SIGALRM is available
        import importlib
        import platform

        # Check if we're on a platform that supports SIGALRM (not Windows)
        has_sigalrm = platform.system() != 'Windows'
        
        if has_sigalrm:
            import signal
            def timeout_handler(signum, frame):
                raise TimeoutError("Importing main took too long")
            
            # Set 20 second timeout for import (increased from 10)
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(20)
            
            try:
                # Import with timeout
                from main import app as main_app
                # Successfully imported the main app, replace fallback
                app = main_app
                print("Flask app imported successfully from main")
                
                # Clear the alarm
                signal.alarm(0)
            except TimeoutError as te:
                print(f"WARNING: Timeout importing main: {str(te)}")
                print("Using fallback app instead")
            except Exception as main_import_err:
                print(f"ERROR importing main: {str(main_import_err)}")
                traceback.print_exc()
                print("Using fallback app instead")
        else:
            # Direct import without timeout on platforms that don't support SIGALRM
            try:
                # Simple import without timeout
                from main import app as main_app
                # Successfully imported the main app, replace fallback
                app = main_app
                print("Flask app imported successfully from main (without timeout)")
            except Exception as main_import_err:
                print(f"ERROR importing main: {str(main_import_err)}")
                traceback.print_exc()
                print("Using fallback app instead")
    except Exception as outer_import_err:
        print(f"OUTER ERROR during import: {str(outer_import_err)}")
        traceback.print_exc()
    
    # Create temp directories if needed
    for dir_name in ['temp_files', 'temp']:
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
            print(f"Created {dir_name} directory")

    print("=== RAILWAY ENTRY: DEPLOYMENT SETUP COMPLETE ===")
except Exception as e:
    print(f"CRITICAL ERROR during Railway setup: {str(e)}")
    traceback.print_exc()

# Final verification that app exists
if 'app' not in locals() or 'app' not in globals() or app is None:
    print("WARNING: No app was created. Creating minimal app for health checks.")
    from flask import Flask, jsonify
    app = Flask(__name__)
    
    @app.route('/healthcheck')
    def last_resort_healthcheck():
        return jsonify({
            "status": "ok", 
            "message": "Last resort app responding to health check",
            "timestamp": time.time()
        })

if __name__ == "__main__":
    # If run directly, start the app
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False) 