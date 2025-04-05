#!/usr/bin/env python3
"""
Railway entry point that applies all compatibility patches
and makes the Flask app available for gunicorn
"""
import os
import sys
import traceback

# Enable verbose logging
os.environ["PYTHONUNBUFFERED"] = "1"

print("=== RAILWAY ENTRY: STARTING DEPLOYMENT SETUP ===")

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
    import wrapper  # This will apply all the compatibility patches
    print("Wrapper imported successfully")

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
    import google.generativeai
    
    # Check for needed features
    print(f"google.generativeai exists: {hasattr(sys.modules, 'google.generativeai')}")
    print(f"types module exists: {hasattr(google.generativeai, 'types')}")
    print(f"GenerateContentConfig exists: {hasattr(google.generativeai.types, 'GenerateContentConfig')}")
    print(f"generate_content exists: {hasattr(google.generativeai, 'generate_content')}")
    print(f"Client exists: {hasattr(google.generativeai, 'Client')}")
    print(f"GenerativeModel exists: {hasattr(google.generativeai, 'GenerativeModel')}")
    
    # Now import the Flask app from main
    print("Importing Flask app from main...")
    from main import app
    print("Flask app imported successfully")
    
    # Create temp directory if needed
    if not os.path.exists('temp_files'):
        os.makedirs('temp_files')
        print("Created temp_files directory")

    print("=== RAILWAY ENTRY: DEPLOYMENT SETUP COMPLETE ===")
except Exception as e:
    print(f"CRITICAL ERROR during Railway setup: {str(e)}")
    traceback.print_exc()
    # Even with error, try to import app for gunicorn
    try:
        from main import app
    except Exception as inner_e:
        print(f"Could not import app: {str(inner_e)}")
        # Create a minimal Flask app for the healthcheck
        from flask import Flask, jsonify
        app = Flask(__name__)
        
        @app.route('/healthcheck')
        def healthcheck():
            return jsonify({"status": "error", "message": "Application failed to initialize correctly"})

if __name__ == "__main__":
    # If run directly, start the app
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False) 