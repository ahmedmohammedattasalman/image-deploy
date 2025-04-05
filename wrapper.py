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

# ========================
# MONKEY PATCH GOOGLE GENERATIVE AI
# This needs to run before any other imports to ensure compatibility
# ========================
def setup_google_genai_compatibility():
    print("Setting up Google Generative AI compatibility...")
    try:
        # First try to directly import the module
        import google.generativeai
        
        # Monkey patch: directly add generate_content if it doesn't exist
        if not hasattr(google.generativeai, 'generate_content'):
            import types
            
            print("WARNING: generate_content method missing, adding compatibility layer")
            
            # Create a direct generate_content function
            def generate_content_impl(prompt, image=None, generation_config=None):
                """Compatibility function for generate_content"""
                try:
                    print(f"Using direct compatibility function for generate_content")
                    # Try to use the generation API in the appropriate method for the current version
                    if hasattr(google.generativeai, 'GenerativeModel'):
                        # For v0.4.0+ style API
                        model = google.generativeai.GenerativeModel('gemini-pro-vision' if image else 'gemini-pro')
                        
                        # Create content list
                        contents = [prompt]
                        if image:
                            contents.append(image)
                            
                        return model.generate_content(
                            contents=contents,
                            generation_config=generation_config
                        )
                    else:
                        print("WARNING: Neither generate_content nor GenerativeModel found!")
                        
                        # As a last resort, create a mock response
                        class MockResponse:
                            def __init__(self):
                                self.candidates = [MockCandidate()]
                        
                        class MockCandidate:
                            def __init__(self):
                                self.content = MockContent()
                        
                        class MockContent:
                            def __init__(self):
                                self.parts = [MockPart()]
                        
                        class MockPart:
                            def __init__(self):
                                self.text = "Error: Unable to use Gemini API in this environment"
                                self.inline_data = None
                        
                        return MockResponse()
                except Exception as e:
                    print(f"Error in generate_content compatibility: {e}")
                    raise
            
            # Add this function to the google.generativeai module
            google.generativeai.generate_content = generate_content_impl
            print("Added generate_content patched function to google.generativeai")
        
        # Also patch Client if needed
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
                    
                    # Use the patched function
                    return google.generativeai.generate_content(
                        prompt=prompt_text, 
                        image=image, 
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
            print("Added Client patched class to google.generativeai")
        
        # Make it available as google.genai for compatibility
        sys.modules["google.genai"] = google.generativeai
        # Also try to make it available directly in the google namespace
        import google
        google.genai = google.generativeai
        print("Successfully set up google.genai compatibility layer")
        return True
    except ImportError as e:
        print(f"Warning: Could not set up google.genai compatibility: {e}")
        try:
            # Try to install the package if it's missing
            import subprocess
            print("Attempting to install required Google packages...")
            subprocess.check_call([
                sys.executable, "-m", "pip", "install", "--quiet",
                "google-generativeai==0.3.1"
            ])
            print("Installed google-generativeai==0.3.1")
            
            # Try import again after installation
            import google.generativeai
            
            # Proceed with the same patches as above
            if not hasattr(google.generativeai, 'generate_content'):
                print("Adding generate_content method to newly installed package")
                
                def generate_content_impl(prompt, image=None, generation_config=None):
                    print(f"Using direct compatibility function for generate_content (post-install)")
                    try:
                        # Try to use the generation API in the available method
                        if hasattr(google.generativeai, 'GenerativeModel'):
                            model = google.generativeai.GenerativeModel('gemini-pro-vision' if image else 'gemini-pro')
                            
                            contents = [prompt]
                            if image:
                                contents.append(image)
                                
                            return model.generate_content(
                                contents=contents,
                                generation_config=generation_config
                            )
                        else:
                            print("WARNING: No appropriate generation methods found!")
                            # Create a mock response as a last resort
                            class MockResponse:
                                def __init__(self):
                                    self.candidates = [MockCandidate()]
                            
                            class MockCandidate:
                                def __init__(self):
                                    self.content = MockContent()
                            
                            class MockContent:
                                def __init__(self):
                                    self.parts = [MockPart()]
                            
                            class MockPart:
                                def __init__(self):
                                    self.text = "Error: Unable to use Gemini API in this environment"
                                    self.inline_data = None
                            
                            return MockResponse()
                    except Exception as e:
                        print(f"Error in generate_content compatibility (post-install): {e}")
                        raise
                
                # Add this function to the google.generativeai module
                google.generativeai.generate_content = generate_content_impl
            
            # Also patch Client class
            if not hasattr(google.generativeai, 'Client'):
                print("Adding Client class to newly installed package")
                
                # Create ModelsClass and ClientCompat classes
                class ModelsClass:
                    def __init__(self, parent_client):
                        self.parent_client = parent_client
                        
                    def generate_content(self, model, contents, config=None):
                        """Compatibility wrapper for generate_content"""
                        print(f"Using compatibility layer for generate_content with model: {model}")
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
                        return google.generativeai.generate_content(
                            prompt=prompt_text, 
                            image=image, 
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
            return True
        except Exception as e2:
            print(f"Error setting up Google Generative AI: {e2}")
            # Continue anyway, the main app will handle the error
            return False

# Run the compatibility setup
setup_success = setup_google_genai_compatibility()

# Now execute the main application
if __name__ == "__main__":
    print("Starting main application...")
    if setup_success:
        import main
        # If main has an app object (Flask app), run it
        if hasattr(main, 'app'):
            host = os.environ.get('HOST', '0.0.0.0')
            port = int(os.environ.get('PORT', 8080))
            debug = os.environ.get('DEBUG', 'False').lower() in ('true', '1', 't')
            main.app.run(host=host, port=port, debug=debug)
    else:
        print("ERROR: Failed to set up Gemini compatibility layer. Application may not work correctly.") 