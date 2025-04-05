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
    
    # Add Client compatibility for older versions
    if not hasattr(google.generativeai, 'Client'):
        print("Adding Client compatibility to google.generativeai")
        
        # Create a ModelsClass with generate_content method
        class ModelsClass:
            def __init__(self, parent_client):
                self.parent_client = parent_client
                
            def generate_content(self, model, contents, config=None):
                """Compatibility wrapper for generate_content"""
                print(f"Using compatibility layer for generate_content with model: {model}")
                # In older versions, generate_content is directly on the generativeai module
                prompt_text = contents[0] if isinstance(contents, list) and contents else ""
                image = contents[1] if isinstance(contents, list) and len(contents) > 1 else None
                
                # Get generation config parameters
                generation_config = {}
                if config:
                    if hasattr(config, 'temperature'):
                        generation_config['temperature'] = config.temperature
                    if hasattr(config, 'top_k'):
                        generation_config['top_k'] = config.top_k
                    if hasattr(config, 'top_p'):
                        generation_config['top_p'] = config.top_p
                
                # Use the direct function from the older version
                if image:
                    return google.generativeai.generate_content(
                        prompt_text, 
                        image, 
                        generation_config=generation_config
                    )
                else:
                    return google.generativeai.generate_content(
                        prompt_text, 
                        generation_config=generation_config
                    )
                
        # Create a Client class that works with the older API
        class ClientCompat:
            def __init__(self, api_key):
                self.api_key = api_key
                # Configure the API with the key
                google.generativeai.configure(api_key=api_key)
                # Create models property with generate_content
                self._models = ModelsClass(self)
                
            # Forward the models attribute to our custom class
            @property
            def models(self):
                return self._models
        
        # Add Client to the google.generativeai module
        google.generativeai.Client = ClientCompat
    
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
            "google-generativeai==0.3.1"
        ])
        # Try import again after installation
        import google.generativeai
        
        # Add Client compatibility for older versions
        if not hasattr(google.generativeai, 'Client'):
            print("Adding Client compatibility to google.generativeai")
            
            # Create a ModelsClass with generate_content method
            class ModelsClass:
                def __init__(self, parent_client):
                    self.parent_client = parent_client
                    
                def generate_content(self, model, contents, config=None):
                    """Compatibility wrapper for generate_content"""
                    print(f"Using compatibility layer for generate_content with model: {model}")
                    # In older versions, generate_content is directly on the generativeai module
                    prompt_text = contents[0] if isinstance(contents, list) and contents else ""
                    image = contents[1] if isinstance(contents, list) and len(contents) > 1 else None
                    
                    # Get generation config parameters
                    generation_config = {}
                    if config:
                        if hasattr(config, 'temperature'):
                            generation_config['temperature'] = config.temperature
                        if hasattr(config, 'top_k'):
                            generation_config['top_k'] = config.top_k
                        if hasattr(config, 'top_p'):
                            generation_config['top_p'] = config.top_p
                    
                    # Use the direct function from the older version
                    if image:
                        return google.generativeai.generate_content(
                            prompt_text, 
                            image, 
                            generation_config=generation_config
                        )
                    else:
                        return google.generativeai.generate_content(
                            prompt_text, 
                            generation_config=generation_config
                        )
            
            # Create a Client class that works with the older API
            class ClientCompat:
                def __init__(self, api_key):
                    self.api_key = api_key
                    # Configure the API with the key
                    google.generativeai.configure(api_key=api_key)
                    # Create models property with generate_content
                    self._models = ModelsClass(self)
                    
                # Forward the models attribute to our custom class
                @property
                def models(self):
                    return self._models
            
            # Add Client to the google.generativeai module
            google.generativeai.Client = ClientCompat
        
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