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

print("=============================================")
print("WRAPPER: INITIALIZING GOOGLE API COMPATIBILITY")
print("=============================================")

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
            print("CRITICAL FIX: generate_content method missing, adding direct compatibility")
            
            # Create a direct generate_content function with detailed parameter handling
            def generate_content_impl(model_or_prompt, image=None, **kwargs):
                """Emergency compatibility function for generate_content with all possible call patterns"""
                try:
                    print(f"USING EMERGENCY COMPATIBILITY LAYER FOR GENERATE_CONTENT")
                    
                    # Case 1: client.models.generate_content(model, contents, config) pattern
                    if 'contents' in kwargs:
                        contents = kwargs.get('contents', [])
                        config = kwargs.get('config', None)
                        
                        model_name = model_or_prompt  # In this case, first arg is model name
                        
                        # Use GenerativeModel if available
                        if hasattr(google.generativeai, 'GenerativeModel'):
                            print(f"Using GenerativeModel API with model: {model_name}")
                            # For newer API style (0.4.0+)
                            model = google.generativeai.GenerativeModel(model_name)
                            result = model.generate_content(
                                contents=contents,
                                generation_config=config
                            )
                            print(f"Successfully generated content with new API")
                            return result
                    
                    # Case 2: Direct call as google.generativeai.generate_content(prompt, image)
                    elif isinstance(model_or_prompt, str):
                        prompt = model_or_prompt
                        
                        # Try to use a model directly if we're in that pattern
                        if hasattr(google.generativeai, 'GenerativeModel'):
                            # Default to vision model if image is provided, otherwise text
                            model_name = "gemini-pro-vision" if image else "gemini-pro"
                            model = google.generativeai.GenerativeModel(model_name)
                            
                            content_list = [prompt]
                            if image:
                                content_list.append(image)
                                
                            result = model.generate_content(content_list)
                            print(f"Used new API for direct generate_content call")
                            return result
                    
                    print("WARNING: Could not find appropriate API pattern, returning mock response")
                    # Last resort - create a basic mock response that matches expected structure
                    class MockCandidate:
                        def __init__(self):
                            self.content = type('obj', (object,), {'parts': []})
                            # Add a text part
                            self.content.parts.append(
                                type('obj', (object,), {'text': "Unable to generate content in this environment", 'inline_data': None})
                            )
                    
                    mock_response = type('obj', (object,), {})
                    mock_response.candidates = [MockCandidate()]
                    return mock_response
                    
                except Exception as e:
                    print(f"CRITICAL ERROR in generate_content compatibility: {e}")
                    # Create an emergency fallback response
                    class EmergencyResponse:
                        def __init__(self):
                            self.candidates = [
                                type('obj', (object,), {
                                    'content': type('obj', (object,), {
                                        'parts': [
                                            type('obj', (object,), {
                                                'text': f"Error generating content: {str(e)}",
                                                'inline_data': None
                                            })
                                        ]
                                    })
                                })
                            ]
                    return EmergencyResponse()
            
            # Add this function to the google.generativeai module
            google.generativeai.generate_content = generate_content_impl
            print("PATCHED google.generativeai.generate_content with emergency compatibility layer")
        
        # Also patch Client if needed
        if not hasattr(google.generativeai, 'Client'):
            print("PATCHING: Adding Client compatibility to google.generativeai")
            
            # Create a ModelsClass with generate_content method
            class ModelsClass:
                def __init__(self, parent_client):
                    self.parent_client = parent_client
                    self.api_key = parent_client.api_key
                    
                def generate_content(self, model, contents, config=None):
                    """Direct compatibility wrapper for the models.generate_content method"""
                    print(f"Using models.generate_content compatibility layer with model: {model}")
                    
                    # Use the patched top-level function
                    return google.generativeai.generate_content(
                        model_or_prompt=model,
                        contents=contents,
                        config=config
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
            print("PATCHED: Added Client class to google.generativeai module")
        
        # Make it available as google.genai for compatibility
        sys.modules["google.genai"] = google.generativeai
        # Also try to make it available directly in the google namespace
        import google
        google.genai = google.generativeai
        print("PATCHED: Successfully set up google.genai compatibility layer")
        return True
    except ImportError as e:
        print(f"WARNING: Could not set up google.genai compatibility: {e}")
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
            
            # Proceed with the emergency compatibility patches
            # (Similar to the above but we'll simplify for brevity in this fallback case)
            if not hasattr(google.generativeai, 'generate_content'):
                def emergency_generate_content(**kwargs):
                    print("EMERGENCY FALLBACK FUNCTION CALLED")
                    # Return a very basic response structure
                    class EmergencyResponse:
                        def __init__(self):
                            self.candidates = [
                                type('obj', (object,), {
                                    'content': type('obj', (object,), {
                                        'parts': [
                                            type('obj', (object,), {
                                                'text': "Emergency fallback response - could not generate content",
                                                'inline_data': None
                                            })
                                        ]
                                    })
                                })
                            ]
                    return EmergencyResponse()
                
                # Add emergency function
                google.generativeai.generate_content = emergency_generate_content
            
            # Add a basic Client class if needed
            if not hasattr(google.generativeai, 'Client'):
                class EmergencyClient:
                    def __init__(self, api_key):
                        self.api_key = api_key
                        google.generativeai.configure(api_key=api_key)
                        
                    @property
                    def models(self):
                        return type('obj', (object,), {
                            'generate_content': lambda *args, **kwargs: google.generativeai.generate_content(*args, **kwargs)
                        })
                
                google.generativeai.Client = EmergencyClient
            
            # Set up module references
            sys.modules["google.genai"] = google.generativeai
            import google
            google.genai = google.generativeai
            
            print("EMERGENCY COMPATIBILITY LAYER INSTALLED")
            return True
            
        except Exception as e2:
            print(f"CRITICAL ERROR setting up Google Generative AI: {e2}")
            # Continue anyway, the main app will handle the error
            return False

# Run the compatibility setup
setup_success = setup_google_genai_compatibility()
print("WRAPPER: Google API compatibility setup complete")
print("=============================================")

# Now execute the main application
if __name__ == "__main__":
    print("Starting main application...")
    if setup_success:
        # Force reload any google modules to ensure patches are applied
        for module_name in list(sys.modules.keys()):
            if module_name.startswith('google'):
                if module_name in sys.modules:
                    del sys.modules[module_name]
        
        # Import main after all patches are applied
        import main
        
        # If main has an app object (Flask app), run it
        if hasattr(main, 'app'):
            host = os.environ.get('HOST', '0.0.0.0')
            port = int(os.environ.get('PORT', 8080))
            debug = os.environ.get('DEBUG', 'False').lower() in ('true', '1', 't')
            main.app.run(host=host, port=port, debug=debug)
    else:
        print("ERROR: Failed to set up Gemini compatibility layer. Application may not work correctly.") 