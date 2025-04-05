#!/usr/bin/env python3
# Emergency Google Generative AI patching
# This runs FIRST before anything else to ensure compatibility
import sys
print("MAIN.PY: Emergency Gemini API compatibility check running...")
try:
    import google.generativeai
    
    # Check for types module and GenerateContentConfig
    try:
        from google.generativeai import types
        if not hasattr(types, 'GenerateContentConfig'):
            print("MAIN.PY CRITICAL: Adding GenerateContentConfig class")
            
            # Create a minimal GenerateContentConfig class
            class GenerateContentConfig:
                def __init__(self, response_modalities=None, temperature=None, top_k=None, top_p=None, **kwargs):
                    self.response_modalities = response_modalities
                    self.temperature = temperature
                    self.top_k = top_k
                    self.top_p = top_p
                    # Store any additional kwargs
                    for key, value in kwargs.items():
                        setattr(self, key, value)
            
            # Add class to types module
            types.GenerateContentConfig = GenerateContentConfig
            print("MAIN.PY: Successfully added GenerateContentConfig class")
    except ImportError:
        print("MAIN.PY WARNING: google.generativeai.types module not found, creating...")
        # Create and inject the types module
        types_module = type('types', (), {})
        
        # Create the GenerateContentConfig class
        class GenerateContentConfig:
            def __init__(self, response_modalities=None, temperature=None, top_k=None, top_p=None, **kwargs):
                self.response_modalities = response_modalities
                self.temperature = temperature
                self.top_k = top_k
                self.top_p = top_p
                # Store any additional kwargs
                for key, value in kwargs.items():
                    setattr(self, key, value)
        
        # Add class to module
        types_module.GenerateContentConfig = GenerateContentConfig
        
        # Inject the types module into google.generativeai
        google.generativeai.types = types_module
        # Also make it importable
        sys.modules['google.generativeai.types'] = types_module
        print("MAIN.PY: Created google.generativeai.types module with GenerateContentConfig")
    
    # Direct high-priority patch for generate_content
    if not hasattr(google.generativeai, 'generate_content'):
        print("MAIN.PY CRITICAL: generate_content missing - applying emergency patch!")
        
        # Check if we have GenerativeModel available (newer API)
        if hasattr(google.generativeai, 'GenerativeModel'):
            def patched_generate_content(prompt_or_model, image=None, **kwargs):
                """Global emergency replacement for generate_content"""
                try:
                    print("Using emergency patched generate_content in main.py")
                    
                    # Detect if this is the client.models.generate_content(model, contents) pattern
                    if 'contents' in kwargs:
                        model_name = prompt_or_model  # In this case it's the model name
                        contents = kwargs.get('contents', [])
                        config = kwargs.get('config', None)
                        
                        # Convert config object to kwargs if needed
                        generation_config = {}
                        if config:
                            # Extract attributes from the config object
                            if hasattr(config, 'temperature') and config.temperature is not None:
                                generation_config['temperature'] = config.temperature
                            if hasattr(config, 'top_k') and config.top_k is not None:
                                generation_config['top_k'] = config.top_k
                            if hasattr(config, 'top_p') and config.top_p is not None:
                                generation_config['top_p'] = config.top_p
                        
                        # Use the newer API with GenerativeModel
                        model = google.generativeai.GenerativeModel(model_name)
                        return model.generate_content(
                            contents=contents,
                            generation_config=generation_config
                        )
                    
                    # Handle the older direct generate_content(prompt, image) pattern
                    else:
                        prompt = prompt_or_model  # In this case it's the prompt text
                        # Default to vision model if image provided
                        model_name = "gemini-pro-vision" if image else "gemini-pro"
                        model = google.generativeai.GenerativeModel(model_name)
                        
                        # Build content list
                        content_list = [prompt]
                        if image:
                            content_list.append(image)
                        
                        # Generate the content with the newer API
                        return model.generate_content(content_list)
                
                except Exception as e:
                    print(f"CRITICAL ERROR in patched generate_content: {e}")
                    # Create a minimal response structure that won't crash
                    class MockResponse:
                        def __init__(self):
                            self.candidates = [{
                                'content': {
                                    'parts': [{
                                        'text': f"ERROR: Failed to generate content - {str(e)}",
                                        'inline_data': None
                                    }]
                                }
                            }]
                    return MockResponse()
            
            # Add the patched function directly to the module
            google.generativeai.generate_content = patched_generate_content
            print("MAIN.PY: Successfully patched generate_content")
        else:
            print("MAIN.PY WARNING: Neither generate_content nor GenerativeModel available!")
    else:
        print("MAIN.PY: generate_content already exists - no patching needed")

except ImportError as ie:
    print(f"MAIN.PY ERROR: Cannot import google.generativeai: {ie}")
except Exception as e:
    print(f"MAIN.PY ERROR during emergency patching: {e}")

# Now continue with the regular imports
import os 
import tempfile
import uuid
import importlib
from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify, send_from_directory, session
import io
from google import genai
from google.genai import types
from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageEnhance, ImageOps
from io import BytesIO
import base64
import time
import shutil
import re
import textwrap
# Supabase compatibility layer - try different package names
try:
    from supabase import create_client
    print("Using supabase package")
except ImportError:
    try:
        from python_supabase import create_client
        print("Using python-supabase package")
    except ImportError:
        try:
            # If using raw dependencies, manually construct a compatible interface
            from postgrest import PostgrestClient
            import gotrue
            import storage3  
            
            def create_client(url, key):
                """Compatibility shim for supabase packages"""
                print("Using manual supabase client implementation")
                class SupabaseStorageContainer:
                    def __init__(self, storage_client, bucket_name):
                        self.storage_client = storage_client
                        self.bucket_name = bucket_name
                    
                    def upload(self, path, file_content, options=None):
                        return self.storage_client.upload(self.bucket_name, path, file_content, options)
                    
                    def download(self, path):
                        return self.storage_client.download(self.bucket_name, path)
                    
                    def get_public_url(self, path):
                        return f"{url}/storage/v1/object/public/{self.bucket_name}/{path}"

                class SupabaseStorageClient:
                    def __init__(self, storage_client):
                        self.storage_client = storage_client
                    
                    def from_(self, bucket_name):
                        return SupabaseStorageContainer(self.storage_client, bucket_name)

                class SupabaseClient:
                    def __init__(self, url, key):
                        self.url = url
                        self.key = key
                        self.auth = gotrue.Auth(url, key)
                        self.storage = SupabaseStorageClient(storage3.StorageClient(url, key))
                        
                    def table(self, table_name):
                        return PostgrestClient(f"{self.url}/rest/v1", headers={
                            "apikey": self.key,
                            "Authorization": f"Bearer {self.key}"
                        }).table(table_name)
                    
                    def query(self, sql_query):
                        # Simple pass-through implementation
                        # In a real app, you'd implement proper SQL execution
                        print(f"SQL query called: {sql_query}")
                        return []

                return SupabaseClient(url, key)
                
        except ImportError:
            print("Warning: No supabase client available. Storage functionality will be disabled.")
            def create_client(url, key):
                raise NotImplementedError("No supabase client is available")
from dotenv import load_dotenv
import requests
import random
import json
from werkzeug.exceptions import RequestEntityTooLarge

# Load environment variables
load_dotenv()

# Language support
TRANSLATIONS = {
    "en": {
        "app_name": "Image Editor",
        "home": "Home",
        "gallery": "Gallery",
        "upload_image": "Upload Your Image",
        "drag_drop": "Drag and drop or click to choose file",
        "image_preview": "Image Preview:",
        "describe_edit": "Describe Your Edit",
        "prompt_placeholder": "Example: Remove the background, Change hair color to blonde, Make it look like a cartoon, etc.",
        "generate_button": "Generate Edited Image",
        "edited_image": "Your Edited Image",
        "slide_compare": "Slide to compare before and after",
        "original": "Original",
        "edited": "Edited",
        "new_image": "New Image",
        "download": "Download",
        "ai_response": "AI Response:",
        "cloud_storage": "Cloud Storage Links:",
        "continue_editing": "Continue Editing",
        "continue_prompt": "Describe your next edit. Example: Now make it black and white, Add a vintage filter, etc.",
        "apply_next": "Apply Next Edit",
        "processing": "Processing your image with AI... This may take a moment",
        "your_gallery": "Your Gallery",
        "gallery_empty": "Your gallery is empty",
        "edited_appear": "Edited images will appear here",
        "powered_by": "Powered by Google Gemini AI | Images stored with",
        "quick_edits": "Quick edits:",
        "bw_edit": "B&W",
        "vintage_edit": "Vintage",
        "painting_edit": "Painting",
        "vignette_edit": "Vignette",
        "contrast_edit": "Contrast",
        "select_image_first": "Please select an image first",
        "continue_info": "You can continue refining your image with additional edits. Each edit builds on the previous result.",
        "edit_history": "Edit History",
        "loading": "Loading..."
    },
    "ar": {
        "app_name": "محرر الصور",
        "home": "الرئيسية",
        "gallery": "المعرض",
        "upload_image": "ارفع صورتك",
        "drag_drop": "اسحب وأفلت أو انقر لاختيار ملف",
        "image_preview": "معاينة الصورة:",
        "describe_edit": "وصف التعديل",
        "prompt_placeholder": "مثال: إزالة الخلفية، تغيير لون الشعر إلى أشقر، اجعله يبدو مثل رسوم متحركة، إلخ.",
        "generate_button": "إنشاء الصورة المعدلة",
        "edited_image": "صورتك المعدلة",
        "slide_compare": "اسحب للمقارنة بين الصورة قبل وبعد",
        "original": "الأصلية",
        "edited": "المعدلة",
        "new_image": "صورة جديدة",
        "download": "تحميل",
        "ai_response": "رد الذكاء الاصطناعي:",
        "cloud_storage": "روابط التخزين السحابي:",
        "continue_editing": "متابعة التحرير",
        "continue_prompt": "صف تعديلك التالي. مثال: الآن اجعلها بالأبيض والأسود، أضف فلتر قديم، إلخ.",
        "apply_next": "تطبيق التعديل التالي",
        "processing": "جاري معالجة صورتك بالذكاء الاصطناعي... قد يستغرق ذلك لحظة",
        "your_gallery": "معرض صورك",
        "gallery_empty": "معرض صورك فارغ",
        "edited_appear": "ستظهر الصور المعدلة هنا",
        "powered_by": "مشغل بواسطة Google Gemini AI | الصور مخزنة باستخدام",
        "quick_edits": "تعديلات سريعة:",
        "bw_edit": "أبيض وأسود",
        "vintage_edit": "قديم",
        "painting_edit": "لوحة",
        "vignette_edit": "فنييت",
        "contrast_edit": "تباين",
        "select_image_first": "يرجى اختيار صورة أولاً",
        "continue_info": "يمكنك متابعة تحسين صورتك بتعديلات إضافية. كل تعديل يبني على النتيجة السابقة.",
        "edit_history": "سجل التعديلات",
        "loading": "جاري التحميل..."
    }
}

# Function to get language text
def get_text(key, lang="en"):
    if lang in TRANSLATIONS and key in TRANSLATIONS[lang]:
        return TRANSLATIONS[lang][key]
    return TRANSLATIONS["en"][key]  # Fallback to English

# Configuration
API_KEY = os.environ.get("API_KEY", "AIzaSyBbE0FW-7SEm1FW0NgusR18GmsV10aAVYE")

# Supabase Configuration
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://ydmzuujthdrokuosbvyt.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlkbXp1dWp0aGRyb2t1b3Nidnl0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDMzNDA0OTMsImV4cCI6MjA1ODkxNjQ5M30.YYtcgWWV59AcM30JUbq91yYVgGGkU8pk3kNofiZC19I")

# Initialize Supabase client with a function to allow reconnection
def get_supabase_client():
    try:
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"Error initializing Supabase client: {str(e)}")
        return None

supabase = get_supabase_client()

# Create temporary directory for session (still needed for temporary operations)
try:
    TEMP_FOLDER = tempfile.mkdtemp()
    os.makedirs(TEMP_FOLDER, exist_ok=True)  # Ensure the directory exists
    print(f"Created temporary directory: {TEMP_FOLDER}")
except Exception as e:
    print(f"Error creating temp directory: {str(e)}")
    # Fallback to a directory in the current folder
    TEMP_FOLDER = os.path.join(os.getcwd(), 'temp_files')
    os.makedirs(TEMP_FOLDER, exist_ok=True)
    print(f"Using fallback directory: {TEMP_FOLDER}")

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Initialize Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 150 * 1024 * 1024  # 150MB max upload size
app.config['SERVER_NAME'] = None  # Prevent issues with request handling
app.config['UPLOAD_FOLDER'] = TEMP_FOLDER  # Explicit temp folder for uploads
app.config['SESSION_TYPE'] = 'filesystem'  # For session storage
app.secret_key = 'image_enhancement_secret_key'  # Secret key for session

# Initialize Gemini client
client = genai.Client(api_key=API_KEY)

# Language route
@app.route('/set_language/<lang>')
def set_language(lang):
    if lang in TRANSLATIONS:
        session['lang'] = lang
    else:
        session['lang'] = 'en'  # Default to English if language not supported
    
    # Redirect back to the referring page or home
    referrer = request.referrer or url_for('index')
    return redirect(referrer)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Helper to convert base64 to image
def base64_to_image(base64_str):
    # Remove data URI prefix if present
    if 'base64,' in base64_str:
        base64_str = base64_str.split('base64,')[1]
    
    # Handle potential padding issues
    missing_padding = len(base64_str) % 4
    if missing_padding:
        base64_str += '=' * (4 - missing_padding)
    
    # Decode base64 to binary
    try:
        img_data = base64.b64decode(base64_str)
        
        # Check if the image data is too large (>5MB)
        if len(img_data) > 5 * 1024 * 1024:
            print(f"Large image data detected: {len(img_data)/1024/1024:.2f}MB, applying aggressive compression")
        
        img = Image.open(BytesIO(img_data))
        
        # Compress the image regardless of size for consistent handling
        max_size_mb = 1.0 if len(img_data) > 5 * 1024 * 1024 else 1.5
        quality = 50 if len(img_data) > 5 * 1024 * 1024 else 60
        
        return compress_image(img, max_size_mb=max_size_mb, quality=quality)
        
    except Exception as e:
        print(f"Error decoding base64 image: {str(e)}")
        # Return a placeholder image or raise the error
        raise ValueError(f"Failed to decode base64 image: {str(e)}")

# Function to compress and resize large images
def compress_image(image, max_size_mb=1.5, quality=60):
    """
    Compress and resize image to reduce its size
    
    Args:
        image: PIL Image object
        max_size_mb: Maximum size in MB
        quality: JPEG compression quality (1-100)
    
    Returns:
        Compressed PIL Image object
    """
    # Convert to RGB if it's not
    if image.mode != 'RGB':
        image = image.convert('RGB')
    
    # Start with original size
    width, height = image.size
    max_pixels = 1200  # Maximum dimension for any side - reduced from 1500
    
    # First resize if necessary to keep dimensions reasonable
    if width > max_pixels or height > max_pixels:
        if width > height:
            new_width = max_pixels
            new_height = int(height * (max_pixels / width))
        else:
            new_height = max_pixels
            new_width = int(width * (max_pixels / height))
        
        image = image.resize((new_width, new_height), Image.LANCZOS)
    
    # Check if we need to compress
    buffered = BytesIO()
    image.save(buffered, format="JPEG", quality=quality, optimize=True)
    img_size_mb = len(buffered.getvalue()) / (1024 * 1024)
    
    # If still too large, reduce quality iteratively and maybe resize further
    if img_size_mb > max_size_mb:
        # If quality is already quite low but file is still large, reduce dimensions further
        if quality < 45:
            # Reduce dimensions by 50%
            new_width = int(image.width * 0.5)
            new_height = int(image.height * 0.5)
            image = image.resize((new_width, new_height), Image.LANCZOS)
            # Try again with reduced size but reset quality
            return compress_image(image, max_size_mb, 60)
        else:
            # Try with lower quality first
            return compress_image(image, max_size_mb, max(30, quality-25))
    
    # Return compressed image
    buffered.seek(0)
    return Image.open(buffered)

# Helper to convert image to base64
def image_to_base64(img, format="PNG", quality=60):
    buffered = BytesIO()
    
    # Compress large images to JPEG with specified quality
    if img.width * img.height > 500000:  # Images larger than ~0.5 megapixels (reduced threshold)
        # Convert to RGB if necessary for JPEG
        if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
            bg = Image.new('RGB', img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[3] if img.mode == 'RGBA' else None)
            img = bg
        
        # If the image is very large, resize it before base64 encoding
        if img.width * img.height > 1000000:  # > 1MP
            max_dim = 1000
            if img.width > img.height:
                new_width = max_dim
                new_height = int(img.height * (max_dim / img.width))
            else:
                new_height = max_dim
                new_width = int(img.width * (max_dim / img.height))
            
            img = img.resize((new_width, new_height), Image.LANCZOS)
        
        format = "JPEG"
        img.save(buffered, format=format, quality=quality, optimize=True)
    else:
        # For smaller images, keep the PNG format for better quality but still optimize
        img.save(buffered, format="PNG", optimize=True, compress_level=9)
    
    # Get the buffer size
    buffer_size = len(buffered.getvalue()) / (1024 * 1024)  # Size in MB
    
    # If the buffer is still too large, compress further
    if buffer_size > 3.0:
        # Reset the buffer
        buffered.close()
        buffered = BytesIO()
        
        # Convert to JPEG with lower quality
        if img.mode in ('RGBA', 'LA') or (img.mode == 'P' and 'transparency' in img.info):
            bg = Image.new('RGB', img.size, (255, 255, 255))
            bg.paste(img, mask=img.split()[3] if img.mode == 'RGBA' else None)
            img = bg
        
        # Resize image to half size if it's still too large
        if img.width * img.height > 800000:
            img = img.resize((img.width // 2, img.height // 2), Image.LANCZOS)
        
        img.save(buffered, format="JPEG", quality=50, optimize=True)
    
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

# Helper to store image in Supabase
def store_image_supabase(image, image_type="original"):
    """
    Stores an image in Supabase Storage and returns the public URL
    
    Args:
        image: PIL Image object
        image_type: Type of image (original or edited)
    
    Returns:
        Tuple of (image_id, public_url)
    """
    # Get a fresh client for this operation
    supabase_client = get_supabase_client()
    if not supabase_client:
        print("Failed to get Supabase client")
        return None, None
        
    max_retries = 3
    retry_delay = 1  # seconds
    
    for attempt in range(max_retries):
        try:
            # Convert image to bytes
            buffered = BytesIO()
            image.save(buffered, format="PNG")
            img_bytes = buffered.getvalue()
            
            # Generate unique file name
            image_id = str(uuid.uuid4())
            file_name = f"{image_id}.png"
            
            # Upload to Supabase
            bucket_name = "images"
            file_path = f"{image_type}/{file_name}"
            
            # ADDED SAFETY: Check if storage is actually available
            if not hasattr(supabase_client, 'storage') or not supabase_client.storage:
                print("Warning: Supabase storage not available, falling back to local storage")
                # Fall back to local storage
                local_path = os.path.join(TEMP_FOLDER, file_name)
                with open(local_path, 'wb') as f:
                    f.write(img_bytes)
                # Return a local "URL" that will work with send_from_directory
                local_url = f"/temp/{file_name}"
                return image_id, local_url
            
            # Verify from_ method exists
            if not hasattr(supabase_client.storage, 'from_'):
                print("Warning: Supabase storage missing 'from_' method, falling back to local storage")
                # Fall back to local storage
                local_path = os.path.join(TEMP_FOLDER, file_name)
                with open(local_path, 'wb') as f:
                    f.write(img_bytes)
                # Return a local "URL" that will work with send_from_directory
                local_url = f"/temp/{file_name}"
                return image_id, local_url
            
            # Extra safety for better error reporting
            try:
                # Get the bucket object first
                bucket = supabase_client.storage.from_(bucket_name)
                if not bucket:
                    raise ValueError(f"Could not access bucket '{bucket_name}'")
                
                # Verify upload method exists
                if not hasattr(bucket, 'upload'):
                    raise ValueError("Bucket object missing 'upload' method")
                
                # Upload the file to Supabase Storage with retry mechanism
                response = bucket.upload(
                    file_path, 
                    img_bytes, 
                    {"content-type": "image/png"}
                )
                
                # Verify get_public_url method exists
                if not hasattr(bucket, 'get_public_url'):
                    raise ValueError("Bucket object missing 'get_public_url' method")
                
                # Get public URL
                public_url = bucket.get_public_url(file_path)
                
                # Skip database insertion for now as the table might not exist
                # Instead, just return the successful upload information
                print(f"Successfully uploaded image to {file_path}")
                
                return image_id, public_url
            except Exception as storage_err:
                print(f"Supabase storage error: {str(storage_err)}")
                # Fall back to local storage as a last resort
                try:
                    local_path = os.path.join(TEMP_FOLDER, file_name)
                    with open(local_path, 'wb') as f:
                        f.write(img_bytes)
                    # Return a local "URL" that will work with send_from_directory
                    local_url = f"/temp/{file_name}"
                    print(f"Saved to local storage instead: {local_path}")
                    return image_id, local_url
                except Exception as local_err:
                    print(f"Even local storage failed: {str(local_err)}")
                    return None, None
        
        except requests.exceptions.ConnectionError as e:
            if attempt < max_retries - 1:
                # Add jitter to prevent thundering herd
                jitter = random.uniform(0, 0.5)
                sleep_time = retry_delay * (2 ** attempt) + jitter
                print(f"Connection error, retrying in {sleep_time:.2f} seconds... ({attempt+1}/{max_retries})")
                time.sleep(sleep_time)
                # Try to get a fresh client for the next attempt
                supabase_client = get_supabase_client()
            else:
                print(f"Error storing image in Supabase after {max_retries} attempts: {str(e)}")
                # Fall back to local storage as a last resort
                try:
                    local_path = os.path.join(TEMP_FOLDER, file_name)
                    with open(local_path, 'wb') as f:
                        f.write(img_bytes)
                    # Return a local "URL" that will work with send_from_directory
                    local_url = f"/temp/{file_name}"
                    print(f"Saved to local storage instead: {local_path}")
                    return image_id, local_url
                except Exception as local_err:
                    print(f"Even local storage failed: {str(local_err)}")
                    return None, None
        
        except Exception as e:
            print(f"Error storing image in Supabase: {str(e)}")
            # For non-connection errors, we'll still retry but with less backoff
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                # Try to get a fresh client for the next attempt
                supabase_client = get_supabase_client()
            else:
                # Fall back to local storage as a last resort
                try:
                    local_path = os.path.join(TEMP_FOLDER, file_name)
                    with open(local_path, 'wb') as f:
                        f.write(img_bytes)
                    # Return a local "URL" that will work with send_from_directory
                    local_url = f"/temp/{file_name}"
                    print(f"Saved to local storage instead: {local_path}")
                    return image_id, local_url
                except Exception as local_err:
                    print(f"Even local storage failed: {str(local_err)}")
                    return None, None

# Helper to get image from Supabase
def get_image_from_supabase(image_id):
    """
    Gets an image from Supabase Storage by its ID
    
    Args:
        image_id: The unique ID of the image
    
    Returns:
        PIL Image object or None if error
    """
    # Get a fresh client for this operation
    supabase_client = get_supabase_client()
    if not supabase_client:
        return None
        
    max_retries = 3
    retry_delay = 1  # seconds
    
    for attempt in range(max_retries):
        try:
            # Since we don't have a database table yet, construct the file path directly
            # Format: {image_type}/{image_id}.png
            bucket_name = "images"
            
            # Check if it's in the "edited" folder first
            file_path = f"edited/{image_id}.png"
            
            try:
                # Try to download from the "edited" folder
                response = supabase_client.storage.from_(bucket_name).download(file_path)
                return Image.open(BytesIO(response))
            except Exception:
                # If not found, try the "original" folder
                file_path = f"original/{image_id}.png"
                response = supabase_client.storage.from_(bucket_name).download(file_path)
                return Image.open(BytesIO(response))
                
        except requests.exceptions.ConnectionError as e:
            if attempt < max_retries - 1:
                # Add jitter to prevent thundering herd
                jitter = random.uniform(0, 0.5)
                sleep_time = retry_delay * (2 ** attempt) + jitter
                print(f"Connection error, retrying in {sleep_time:.2f} seconds... ({attempt+1}/{max_retries})")
                time.sleep(sleep_time)
                # Try to get a fresh client for the next attempt
                supabase_client = get_supabase_client()
            else:
                print(f"Error retrieving image from Supabase after {max_retries} attempts: {str(e)}")
                return None
        
        except Exception as e:
            print(f"Error retrieving image from Supabase: {str(e)}")
            # For non-connection errors, we'll still retry but with less backoff
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                # Try to get a fresh client for the next attempt
                supabase_client = get_supabase_client()
            else:
                return None

# Cleanup temporary files on shutdown
@app.teardown_appcontext
def cleanup_temp_files(exception=None):
    try:
        if os.path.exists(TEMP_FOLDER) and TEMP_FOLDER != os.path.join(os.getcwd(), 'temp_files'):
            shutil.rmtree(TEMP_FOLDER)
            print(f"Cleaned up temp directory: {TEMP_FOLDER}")
    except Exception as e:
        print(f"Error cleaning up temp directory: {str(e)}")

# Create a sample image
def create_sample_image():
    # Create a sample 500x500 image with some text
    image = Image.new('RGB', (500, 500), color=(73, 109, 137))
    d = ImageDraw.Draw(image)
    
    # Try to use a font, but fall back to default if not available
    try:
        font = ImageFont.truetype("arial.ttf", 36)
    except IOError:
        font = ImageFont.load_default()
    
    d.text((100, 200), "Sample Image", fill=(255, 255, 255), font=font)
    d.text((100, 250), "Use this for testing", fill=(255, 255, 255), font=font)
    
    return image

# Function to format Arabic text for Gemini
def format_arabic_text(text):
    """
    Format Arabic text to ensure proper processing by Gemini.
    Args:
        text: The Arabic text to format
    Returns:
        Formatted Arabic text
    """
    # Check if text is empty
    if not text:
        return text
    
    # Common quick edit phrases in Arabic and their well-formatted equivalents
    quick_edit_phrases = {
        'اجعلها بالأبيض والأسود': 'حول الصورة إلى اللونين الأبيض والأسود',
        'أضف فلتر قديم': 'أضف تأثير الصور القديمة على الصورة',
        'اجعلها تبدو كلوحة فنية': 'حول الصورة إلى لوحة فنية',
        'أضف تأثير فنييت': 'أضف تأثير الفنييت حول حواف الصورة',
        'زيادة التباين': 'قم بزيادة تباين الألوان في الصورة'
    }
    
    # If the text matches one of our quick edit phrases, use the enhanced version
    if text in quick_edit_phrases:
        return quick_edit_phrases[text]
    
    # Otherwise, return the original text
    return text

# Helper function to get text dimensions consistently across PIL versions
def get_text_dimensions(draw, text, font):
    try:
        # Try newer method first
        if hasattr(font, 'getbbox'):
            bbox = font.getbbox(text)
            return bbox[2] - bbox[0], bbox[3] - bbox[1]
        # Fall back to older textsize method
        elif hasattr(draw, 'textsize'):
            return draw.textsize(text, font=font)
        else:
            # Ultimate fallback - estimate based on font size and text length
            return len(text) * font.size // 2, font.size + 4
    except Exception:
        # If all else fails, return a reasonable default
        return 300, 20

@app.route('/', methods=['GET', 'POST'])
def index():
    # Get current language from session or default to English
    lang = session.get('lang', 'en')
    
    if request.method == 'POST':
        try:
            # Check if prompt is provided
            if 'prompt' not in request.form:
                return render_template('index.html', error="Please provide a prompt.", texts=TRANSLATIONS[lang], lang=lang, dir="rtl" if lang == "ar" else "ltr")
            
            prompt = request.form['prompt']
            
            # Check if this is a continued edit - we'll handle both from the same form
            # It will be 'true' if we're continuing an edit from a previous result
            continue_edit = request.form.get('continue_edit') == 'true'
            
            # Initialize previous prompts list
            previous_prompts = []
            
            if continue_edit:
                # Get the previous result from hidden form field
                prev_result_b64 = request.form.get('previous_result_b64', '')
                
                # Get previous prompts if available
                previous_prompts_str = request.form.get('previous_prompts', '')
                if previous_prompts_str:
                    try:
                        previous_prompts = json.loads(previous_prompts_str)
                    except:
                        previous_prompts = []
                
                if not prev_result_b64:
                    return render_template('index.html', error="Previous result not found. Please start with a new image.", texts=TRANSLATIONS[lang], lang=lang, dir="rtl" if lang == "ar" else "ltr")
                
                try:
                    # Save the base64 image to a temporary file to avoid memory issues
                    img_id = str(uuid.uuid4())
                    prev_img_path = os.path.join(TEMP_FOLDER, f"prev_{img_id}.jpg")
                    orig_img_path = os.path.join(TEMP_FOLDER, f"orig_{img_id}.jpg")
                    
                    # Instead of keeping everything in memory, save to disk
                    try:
                        # Process previous result
                        image = base64_to_image(prev_result_b64)
                        image.save(prev_img_path, format="JPEG", quality=60, optimize=True)
                        image = Image.open(prev_img_path)  # Reload from disk
                        
                        # Process original image
                        original_image_b64_raw = request.form.get('original_image_b64', prev_result_b64)
                        original_img = base64_to_image(original_image_b64_raw)
                        original_img.save(orig_img_path, format="JPEG", quality=60, optimize=True)
                        
                        # Load the original image from disk and convert to base64 for display
                        original_img = Image.open(orig_img_path)
                        original_image_b64 = image_to_base64(original_img, quality=60)
                        
                    except Exception as compression_error:
                        print(f"Error during file-based compression: {str(compression_error)}")
                        # Fall back to in-memory processing
                        image = base64_to_image(prev_result_b64)
                        original_img = base64_to_image(request.form.get('original_image_b64', prev_result_b64))
                        original_image_b64 = image_to_base64(original_img, quality=60)
                except Exception as e:
                    return render_template('index.html', error=f"Error processing previous edit: {str(e)}", texts=TRANSLATIONS[lang], lang=lang, dir="rtl" if lang == "ar" else "ltr")
            else:
                # Normal flow - check for file upload
                if 'file' not in request.files:
                    return render_template('index.html', error="Please upload an image.", texts=TRANSLATIONS[lang], lang=lang, dir="rtl" if lang == "ar" else "ltr")
                
                file = request.files['file']
                
                # Check if file is valid
                if file.filename == '':
                    return render_template('index.html', error="No file selected.", texts=TRANSLATIONS[lang], lang=lang, dir="rtl" if lang == "ar" else "ltr")
                
                if not allowed_file(file.filename):
                    return render_template('index.html', error="File type not allowed. Please upload PNG or JPG images.", texts=TRANSLATIONS[lang], lang=lang, dir="rtl" if lang == "ar" else "ltr")
                
                try:
                    # Read the image directly
                    image = Image.open(file.stream)
                    
                    # Compress large images to avoid memory issues
                    if image.width * image.height > 1500000:  # ~1.5 megapixels
                        image = compress_image(image)
                    
                    # Store the original image in Supabase
                    original_id, original_url = None, None
                    try:
                        original_id, original_url = store_image_supabase(image, "original")
                        if not original_url:
                            print("Warning: Failed to store original image in Supabase, continuing with local processing")
                    except Exception as e:
                        print(f"Error storing original image: {str(e)}")
                        # Continue with local processing if Supabase storage fails
                    
                    # Convert to base64 for original image reference with compression if needed
                    original_image_b64 = image_to_base64(image)
                except Exception as e:
                    return render_template('index.html', error=f"Error processing uploaded image: {str(e)}", texts=TRANSLATIONS[lang], lang=lang, dir="rtl" if lang == "ar" else "ltr")
            
            # Add current prompt to previous prompts list
            previous_prompts.append(prompt)
            
            # Process the image with Gemini
            try:
                # Generate content using Gemini with retry mechanism
                max_retries = 3
                retry_delay = 2
                last_error = None
                
                # Prepare the prompt for processing
                # Add special handling for Arabic text by ensuring proper encoding and text direction
                if lang == "ar":
                    # Format the Arabic text to ensure proper processing
                    formatted_prompt = format_arabic_text(prompt)
                    # Add explicit language indicator and instructions for Gemini to handle Arabic text
                    processed_prompt = f"""استخدم اللغة العربية فقط في الرد. 
مهمتك: قم بتحرير الصورة المرفقة حسب الإرشادات التالية:
{formatted_prompt}

قم بمعالجة الصورة وأظهر النتيجة المعدلة. لا تستخدم أي لغة أخرى غير العربية في ردك."""
                    # For debugging
                    print(f"Processing Arabic prompt: {processed_prompt}")
                else:
                    # Improved general prompt that explicitly asks for an image
                    processed_prompt = f"""MOST IMPORTANT: Edit the attached image according to this description: {prompt}

YOU MUST RETURN AN EDITED IMAGE based on the input image. Image generation is required, not optional.

After generating the edited image, briefly explain what changes you made."""
                    print(f"Enhanced prompt: {processed_prompt[:100]}...")
                
                for attempt in range(max_retries):
                    try:
                        # RAILWAY/DEPLOYMENT FIX: Add detailed error handling and logging
                        print(f"Attempt {attempt+1}: Processing image with prompt: {processed_prompt[:100]}...")
                        print(f"Using model: gemini-2.0-flash-exp-image-generation")
                        
                        try:
                            # Improved prompt formatting and image preparation
                            # Convert image to RGB mode for better compatibility
                            if image.mode != 'RGB':
                                image = image.convert('RGB')
                                
                            # Save image to bytes for reliable handling
                            img_byte_arr = BytesIO()
                            image.save(img_byte_arr, format='JPEG', quality=95) 
                            img_byte_arr.seek(0)
                            
                            # Create a properly formatted image part for Gemini
                            image_part = {
                                "mime_type": "image/jpeg",
                                "data": base64.b64encode(img_byte_arr.getvalue()).decode('utf-8')
                            }
                            
                            # CRITICAL: Use the correct model for image editing
                            # gemini-1.5-pro-latest supports image editing better than flash
                            model_name = "gemini-1.5-pro-latest"
                            print(f"Using model: {model_name} for image editing")
                            
                            # First try using the standard client.models.generate_content approach
                            generation_config = types.GenerateContentConfig(
                                temperature=0.4,  # Higher temperature for more creative edits
                                top_k=32,
                                top_p=0.95,
                                max_output_tokens=2048,
                                response_mime_type="image/png"  # Explicitly request image response
                            )
                            
                            safety_settings = [
                                {
                                    "category": "HARM_CATEGORY_HARASSMENT",
                                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                                },
                                {
                                    "category": "HARM_CATEGORY_HATE_SPEECH",
                                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                                },
                                {
                                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                                },
                                {
                                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                                    "threshold": "BLOCK_MEDIUM_AND_ABOVE"
                                }
                            ]
                            
                            # Create an enhanced prompt that explicitly instructs the model to return an image
                            enhanced_prompt = f"""INSTRUCTIONS: Edit the following image as described below. 
You MUST return the edited image and a brief text explanation.

EDIT REQUEST: {prompt}

IMAGE EDITING INSTRUCTIONS:
1. Make the requested changes to the input image
2. Return both the edited image and a text explanation
3. Do not place text on the image itself
4. Return the image in PNG format
5. Maintain the original resolution
6. Ensure the edited image is the first element in your response

This is a direct image editing task that requires you to return a modified version of the input image."""
                            
                            # Structured content with proper format
                            contents = [
                                {
                                    "role": "user", 
                                    "parts": [
                                        {"text": enhanced_prompt},
                                        {"inline_data": image_part}
                                    ]
                                }
                            ]
                            
                            response = client.models.generate_content(
                                model=model_name,
                                contents=contents,
                                generation_config=generation_config,
                                safety_settings=safety_settings
                            )
                            print("Used client.models.generate_content successfully")
                        except Exception as api_error:
                            # If that fails, try our compatibility approach directly
                            print(f"Primary API call failed: {str(api_error)}")
                            print("Using fallback direct GenerativeModel call...")
                            
                            # Create a GenerativeModel directly
                            if hasattr(google.generativeai, 'GenerativeModel'):
                                try:
                                    # Use gemini-1.5-pro which is better for image editing
                                    model = google.generativeai.GenerativeModel(model_name)
                                    
                                    # Generation parameters optimized for image editing
                                    generation_config = {
                                        'temperature': 0.4,
                                        'top_k': 32,
                                        'top_p': 0.95,
                                        'max_output_tokens': 2048,
                                        'response_mime_type': 'image/png'
                                    }
                                    
                                    # Create properly formatted contents
                                    contents = [
                                        {
                                            "role": "user", 
                                            "parts": [
                                                {"text": enhanced_prompt},
                                                {"inline_data": image_part}
                                            ]
                                        }
                                    ]
                                    
                                    # Try with stream=False to ensure we get the full response
                                    response = model.generate_content(
                                        contents=contents,
                                        generation_config=generation_config,
                                        stream=False
                                    )
                                    print("Used GenerativeModel successfully via fallback")
                                except Exception as model_error:
                                    print(f"GenerativeModel direct call failed: {str(model_error)}")
                                    # Try with the original model as last resort
                                    model = google.generativeai.GenerativeModel("gemini-2.0-flash-exp-image-generation")
                                    response = model.generate_content(
                                        contents=contents,
                                        generation_config=generation_config,
                                        stream=False
                                    )
                                    print("Used original model as last resort")
                            else:
                                # Ultimate fallback
                                raise RuntimeError("No compatible API method available")
                        
                        # If we got here, the request succeeded
                        break
                    except Exception as e:
                        last_error = e
                        error_message = str(e)
                        print(f"Error during image processing attempt {attempt+1}: {error_message}")
                        
                        # Check if this is an overload error
                        if "503" in error_message and "overloaded" in error_message.lower():
                            if attempt < max_retries - 1:
                                # Add jitter to prevent thundering herd
                                jitter = random.uniform(0, 1)
                                sleep_time = retry_delay * (2 ** attempt) + jitter
                                print(f"Gemini API overloaded, retrying in {sleep_time:.2f} seconds... (Attempt {attempt+1}/{max_retries})")
                                time.sleep(sleep_time)
                            else:
                                # All retries failed
                                return render_template('index.html', 
                                            error="The AI image generation service is currently experiencing high traffic. Please try again in a few minutes.",
                                            texts=TRANSLATIONS[lang], 
                                            lang=lang, 
                                            dir="rtl" if lang == "ar" else "ltr")
                        else:
                            # For other errors, don't retry
                            raise e
                
                # If we exhausted all retries and still have an error
                if 'response' not in locals():
                    raise last_error
                
                # Print response structure for debugging
                print("Response received, exploring structure...")
                print(f"Response type: {type(response)}")
                if hasattr(response, 'candidates'):
                    print(f"Has candidates: {len(response.candidates) if hasattr(response.candidates, '__len__') else 'Yes'}")
                else:
                    print("No candidates attribute found")
                
                # Process the response
                response_text = ""
                result_image = None
                result_image_b64 = None
                
                try:
                    print("Processing response...")
                    print(f"Response type: {type(response)}")
                    # Add detailed response inspection
                    if hasattr(response, '_raw_response'):
                        print(f"Raw response keys: {list(response._raw_response.keys()) if isinstance(response._raw_response, dict) else 'Not a dictionary'}")
                    
                    # CRITICAL FIX: Improved image extraction from response
                    if hasattr(response, 'candidates') and response.candidates:
                        for candidate_idx, candidate in enumerate(response.candidates):
                            print(f"Processing candidate {candidate_idx+1}/{len(response.candidates)}")
                            
                            if hasattr(candidate, 'content') and candidate.content:
                                for part_idx, part in enumerate(candidate.content.parts):
                                    print(f"Processing part {part_idx+1}/{len(candidate.content.parts)}")
                                    
                                    # Extract text parts
                                    if hasattr(part, 'text') and part.text:
                                        print(f"Found text part: {len(part.text)} chars")
                                        response_text += part.text
                                    
                                    # Extract image with better error handling
                                    if hasattr(part, 'inline_data') and part.inline_data:
                                        try:
                                            print(f"Found inline_data with mime type: {getattr(part.inline_data, 'mime_type', 'unknown')}")
                                            
                                            # Get image data with multiple fallbacks
                                            image_data = None
                                            
                                            # Try method 1: Direct data attribute
                                            if hasattr(part.inline_data, 'data') and part.inline_data.data:
                                                print("Using direct data attribute")
                                                image_data = part.inline_data.data
                                            
                                            # Try method 2: _raw_data attribute 
                                            elif hasattr(part.inline_data, '_raw_data'):
                                                print("Using _raw_data attribute")
                                                image_data = part.inline_data._raw_data
                                                
                                            # Try method 3: Check if inline_data is a string (already base64)
                                            elif isinstance(part.inline_data, str) and len(part.inline_data) > 100:
                                                print("inline_data appears to be a string, treating as base64")
                                                image_data = part.inline_data
                                                
                                            # Try method 4: Check attributes dict
                                            elif hasattr(part.inline_data, '__dict__'):
                                                print("Searching attributes dictionary")
                                                for attr_name, attr_value in part.inline_data.__dict__.items():
                                                    if attr_name.lower().endswith('data') and isinstance(attr_value, (str, bytes)):
                                                        print(f"Found data in attribute: {attr_name}")
                                                        image_data = attr_value
                                                        break
                                            
                                            if image_data:
                                                # Handle both string (base64) and bytes
                                                try:
                                                    if isinstance(image_data, str):
                                                        # Check if it's a data URL
                                                        if image_data.startswith('data:'):
                                                            print("Detected data URL format")
                                                            image_data = image_data.split(',', 1)[1]
                                                        
                                                        # Decode base64 to bytes
                                                        image_bytes = base64.b64decode(image_data)
                                                    else:
                                                        # Already bytes
                                                        image_bytes = image_data
                                                        
                                                    print(f"Extracted image data: {len(image_bytes)} bytes")
                                                    
                                                    # Multiple methods to open the image
                                                    try:
                                                        # Method 1: Direct open
                                                        img_buffer = BytesIO(image_bytes)
                                                        img_buffer.seek(0)
                                                        result_image = Image.open(img_buffer)
                                                        print(f"Successfully opened image via direct method: {result_image.format}, {result_image.size}")
                                                    except Exception as direct_err:
                                                        print(f"Direct open failed: {str(direct_err)}")
                                                        
                                                        try:
                                                            # Method 2: Save to temp file first
                                                            temp_img_path = os.path.join(TEMP_FOLDER, f"temp_result_{uuid.uuid4()}.png")
                                                            with open(temp_img_path, 'wb') as f:
                                                                f.write(image_bytes)
                                                            result_image = Image.open(temp_img_path)
                                                            print(f"Successfully opened image via temp file: {result_image.format}, {result_image.size}")
                                                            # Clean up file after loading
                                                            try:
                                                                os.remove(temp_img_path)
                                                            except:
                                                                pass
                                                        except Exception as temp_err:
                                                            print(f"Temp file method failed: {str(temp_err)}")
                                                            continue  # Try next part if this fails
                                                    
                                                    # Successfully loaded image
                                                    result_image_b64 = image_to_base64(result_image)
                                                    print(f"Successfully converted image to base64 ({len(result_image_b64)} chars)")
                                                    break  # Exit parts loop - we have our image
                                                
                                                except Exception as img_err:
                                                    print(f"Error processing image data: {str(img_err)}")
                                            else:
                                                print("No usable image data found in inline_data")
                                        except Exception as inline_err:
                                            print(f"Error accessing inline_data: {str(inline_err)}")
                            
                            # If we found an image, break out of candidates loop
                            if result_image:
                                break
                    
                    # If we didn't get an image but have raw response, try to extract from there
                    if not result_image and hasattr(response, '_raw_response'):
                        try:
                            print("Attempting extraction from _raw_response...")
                            raw_data = response._raw_response
                            
                            if isinstance(raw_data, dict):
                                # Navigate through the raw response structure
                                if 'candidates' in raw_data:
                                    for candidate in raw_data['candidates']:
                                        if 'content' in candidate and 'parts' in candidate['content']:
                                            for part in candidate['content']['parts']:
                                                if 'inline_data' in part and isinstance(part['inline_data'], dict):
                                                    # Commonly found in Gemini responses
                                                    if 'data' in part['inline_data'] and 'mime_type' in part['inline_data']:
                                                        try:
                                                            print(f"Found image data in raw response: {part['inline_data']['mime_type']}")
                                                            img_data = base64.b64decode(part['inline_data']['data'])
                                                            img_buffer = BytesIO(img_data)
                                                            result_image = Image.open(img_buffer)
                                                            result_image_b64 = image_to_base64(result_image)
                                                            print("Successfully extracted image from raw response")
                                                            break
                                                        except Exception as raw_img_err:
                                                            print(f"Error extracting image from raw data: {str(raw_img_err)}")
                        except Exception as raw_err:
                            print(f"Error processing raw response: {str(raw_err)}")
                    
                    # NEW APPROACH: Last resort - generate our own image from the original with a PIL filter
                    if not result_image_b64:
                        print("No image in response. Applying PIL filter to original image as fallback...")
                        try:
                            # Create a fallback edited image using PIL filters
                            fallback_edited = image.copy()
                            
                            # Apply a filter based on the prompt
                            prompt_lower = prompt.lower()
                            if 'black and white' in prompt_lower or 'grayscale' in prompt_lower or 'bw' in prompt_lower or 'b&w' in prompt_lower:
                                fallback_edited = fallback_edited.convert('L').convert('RGB')
                                filter_used = "grayscale filter"
                            elif 'sepia' in prompt_lower or 'vintage' in prompt_lower or 'old' in prompt_lower:
                                # Apply sepia filter
                                sepia = ImageOps.colorize(ImageOps.grayscale(fallback_edited), "#704214", "#C0A080")
                                fallback_edited = sepia
                                filter_used = "sepia/vintage filter"
                            elif 'bright' in prompt_lower or 'vibrant' in prompt_lower:
                                # Increase brightness and saturation
                                enhancer = ImageEnhance.Brightness(fallback_edited)
                                fallback_edited = enhancer.enhance(1.3)
                                enhancer = ImageEnhance.Color(fallback_edited)
                                fallback_edited = enhancer.enhance(1.5)
                                filter_used = "brightness/saturation enhancement"
                            elif 'contrast' in prompt_lower:
                                # Increase contrast
                                enhancer = ImageEnhance.Contrast(fallback_edited)
                                fallback_edited = enhancer.enhance(1.5)
                                filter_used = "contrast enhancement"
                            elif 'blur' in prompt_lower or 'soft' in prompt_lower:
                                # Apply blur
                                fallback_edited = fallback_edited.filter(ImageFilter.GaussianBlur(radius=2))
                                filter_used = "blur effect"
                            elif 'sharp' in prompt_lower or 'clarity' in prompt_lower:
                                # Sharpen the image
                                fallback_edited = fallback_edited.filter(ImageFilter.SHARPEN)
                                filter_used = "sharpening filter"
                            elif 'painting' in prompt_lower or 'art' in prompt_lower or 'paint' in prompt_lower:
                                # Create painting-like effect
                                fallback_edited = fallback_edited.filter(ImageFilter.CONTOUR)
                                enhancer = ImageEnhance.Color(fallback_edited)
                                fallback_edited = enhancer.enhance(1.4)
                                filter_used = "painting effect"
                            else:
                                # Apply a moderate image enhancement as default
                                enhancer = ImageEnhance.Contrast(fallback_edited)
                                fallback_edited = enhancer.enhance(1.2)
                                enhancer = ImageEnhance.Color(fallback_edited)
                                fallback_edited = enhancer.enhance(1.2)
                                filter_used = "general enhancement"
                            
                            # Add a text overlay with explanation
                            draw = ImageDraw.Draw(fallback_edited)
                            try:
                                font = ImageFont.truetype("arial.ttf", 16)
                            except:
                                font = ImageFont.load_default()
                            
                            # Add watermark at the bottom with translucent background
                            msg = f"Applied {filter_used} [Gemini could not generate a custom edit]"
                            textsize = get_text_dimensions(draw, msg, font)
                            
                            # Create translucent text background
                            try:
                                overlay = Image.new('RGBA', fallback_edited.size, (0, 0, 0, 0))
                                overlay_draw = ImageDraw.Draw(overlay)
                                overlay_draw.rectangle(
                                    [(10, fallback_edited.height - textsize[1] - 30), (textsize[0] + 20, fallback_edited.height - 10)],
                                    fill=(0, 0, 0, 128)
                                )
                                # Convert to RGBA first if needed
                                if fallback_edited.mode != 'RGBA':
                                    fallback_edited = fallback_edited.convert('RGBA')
                                fallback_edited = Image.alpha_composite(fallback_edited, overlay).convert('RGB')
                            except Exception as overlay_err:
                                print(f"Error creating overlay: {str(overlay_err)}")
                                # Fallback to simpler approach without overlay
                                draw.rectangle(
                                    [(10, fallback_edited.height - textsize[1] - 30), (textsize[0] + 20, fallback_edited.height - 10)],
                                    fill=(0, 0, 0)
                                )
                            
                            # Add text
                            draw = ImageDraw.Draw(fallback_edited)
                            draw.text((15, fallback_edited.height - textsize[1] - 20), msg, font=font, fill=(255, 255, 255))
                            
                            # Set as result
                            result_image = fallback_edited
                            result_image_b64 = image_to_base64(result_image)
                            
                            # Create a complementary response text
                            if not response_text:
                                response_text = f"I've applied a {filter_used} to your image based on your request. Here's the result."
                            
                            print(f"Created fallback edited image using {filter_used}")
                        except Exception as fallback_err:
                            print(f"Error creating fallback image: {str(fallback_err)}")
                            
                            # Even more basic fallback - just use text image
                            if response_text:
                                print("Creating fallback text image...")
                                try:
                                    fallback_img = Image.new('RGB', (800, 400), color=(73, 109, 137))
                                    d = ImageDraw.Draw(fallback_img)
                                    try:
                                        font = ImageFont.truetype("arial.ttf", 18)
                                    except:
                                        font = ImageFont.load_default()
                                        
                                    # Display part of the response text on the image
                                    wrapped_text = "\n".join(textwrap.wrap(response_text[:500], width=50))
                                    d.text((20, 20), "Gemini could not generate an image, but provided this response:", fill=(255, 255, 255), font=font)
                                    d.text((20, 60), wrapped_text, fill=(255, 255, 255), font=font)
                                    result_image = fallback_img
                                    result_image_b64 = image_to_base64(result_image)
                                    print("Created fallback text image")
                                except Exception as text_img_err:
                                    print(f"Error creating text image: {str(text_img_err)}")
                
                except (IndexError, AttributeError) as e:
                    # Handle parsing errors with Gemini response
                    print(f"Error parsing Gemini response: {str(e)}")
                    # Try alternate method to extract response
                    try:
                        if hasattr(response, 'text'):
                            response_text = response.text
                        elif hasattr(response, 'candidates') and len(response.candidates) > 0:
                            # Navigate the response structure differently
                            for candidate in response.candidates:
                                if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
                                    for part in candidate.content.parts:
                                        if hasattr(part, 'text') and part.text:
                                            response_text += part.text
                                        elif hasattr(part, 'inline_data') and part.inline_data:
                                            try:
                                                img_bytes = part.inline_data.data
                                                img_buffer = BytesIO(img_bytes)
                                                result_image = Image.open(img_buffer)
                                                result_image_b64 = image_to_base64(result_image)
                                            except Exception as inner_img_err:
                                                print(f"Inner image extraction error: {str(inner_img_err)}")
                    except Exception as inner_e:
                        print(f"Alternative response parsing also failed: {str(inner_e)}")
                
                # FINAL FALLBACK: If nothing else worked, use our local PIL filter
                if not result_image_b64:
                    try:
                        # Apply a simple enhancement to the original image
                        print("FINAL FALLBACK: Applying simple enhancement to original image")
                        enhanced = image.copy()
                        # Apply modest contrast and sharpness increase
                        enhancer = ImageEnhance.Contrast(enhanced)
                        enhanced = enhancer.enhance(1.2)
                        enhanced = enhanced.filter(ImageFilter.SHARPEN)
                        
                        # Add a text overlay explaining the situation
                        draw = ImageDraw.Draw(enhanced)
                        try:
                            font = ImageFont.truetype("arial.ttf", 16)
                        except:
                            font = ImageFont.load_default()
                            
                        text = "Simple enhancement applied (AI edit unavailable)"
                        textsize = get_text_dimensions(draw, text, font)
                        
                        # Create semi-transparent background for text
                        try:
                            overlay = Image.new('RGBA', enhanced.size, (0, 0, 0, 0))
                            draw_overlay = ImageDraw.Draw(overlay)
                            draw_overlay.rectangle(
                                [(10, enhanced.height - textsize[1] - 30), (textsize[0] + 20, enhanced.height - 10)],
                                fill=(0, 0, 0, 128)
                            )
                            enhanced = Image.alpha_composite(enhanced.convert('RGBA'), overlay).convert('RGB')
                        except Exception as overlay_err:
                            print(f"Error creating overlay: {str(overlay_err)}")
                            # Direct drawing without overlay
                            draw.rectangle(
                                [(10, enhanced.height - textsize[1] - 30), (textsize[0] + 20, enhanced.height - 10)],
                                fill=(0, 0, 0)
                            )
                        
                        # Add text
                        draw = ImageDraw.Draw(enhanced)
                        draw.text((15, enhanced.height - textsize[1] - 20), text, font=font, fill=(255, 255, 255))
                        
                        result_image = enhanced
                        result_image_b64 = image_to_base64(result_image)
                        
                        # Create default response if none exists
                        if not response_text:
                            response_text = "I've applied a basic enhancement to your image. For better results, please try a different edit description."
                            
                        print("Created emergency enhanced image")
                    except Exception as final_err:
                        print(f"Even final fallback failed: {str(final_err)}")
                
                if not result_image_b64:
                    # Special message for Arabic users
                    if lang == "ar":
                        error_msg = "فشل في إنشاء الصورة المعدلة. يرجى المحاولة مرة أخرى بتعليمات مختلفة."
                    else:
                        error_msg = "Failed to generate edited image. Please try different instructions."
                    return render_template('index.html', error=error_msg, texts=TRANSLATIONS[lang], lang=lang, dir="rtl" if lang == "ar" else "ltr")
                
                # Store the edited image in Supabase
                edited_id, edited_url = None, None
                if result_image:
                    try:
                        edited_id, edited_url = store_image_supabase(result_image, "edited")
                        if not edited_url:
                            print("Warning: Failed to store edited image in Supabase, continuing with local processing")
                    except Exception as e:
                        print(f"Error storing edited image: {str(e)}")
                        # Continue without Supabase storage if it fails
                
                # If it's not a continued edit, the current image is the first original
                first_original_b64_raw = request.form.get('first_original_b64', original_image_b64)
                
                # Ensure first_original is also compressed if needed
                if continue_edit and first_original_b64_raw:
                    try:
                        first_original_img = base64_to_image(first_original_b64_raw)
                        if first_original_img.width * first_original_img.height > 1500000:
                            first_original_img = compress_image(first_original_img)
                        first_original_b64 = image_to_base64(first_original_img)
                    except:
                        first_original_b64 = original_image_b64
                else:
                    first_original_b64 = original_image_b64
                
                # Convert previous prompts to JSON string for form submission
                previous_prompts_json = json.dumps(previous_prompts)
                
                # Create response with the base64 images and flag for preview update
                return render_template('index.html', 
                                    prompt=prompt, 
                                    original_image_b64=original_image_b64,
                                    result_image_b64=result_image_b64,
                                    first_original_b64=first_original_b64,
                                    response_text=response_text,
                                    is_b64_image=True,
                                    update_preview=True,  # Flag to trigger preview update
                                    previous_prompts=previous_prompts,  # Pass the list of previous prompts
                                    previous_prompts_json=previous_prompts_json,  # Pass as JSON for form submission
                                    supabase_original_url=original_url if 'original_url' in locals() and original_url else None,
                                    supabase_edited_url=edited_url if 'edited_url' in locals() and edited_url else None,
                                    texts=TRANSLATIONS[lang], 
                                    lang=lang, 
                                    dir="rtl" if lang == "ar" else "ltr")
            
            except Exception as e:
                error_message = str(e)
                # Provide a user-friendly message for common errors
                if "503" in error_message and "overloaded" in error_message.lower():
                    if lang == "ar":
                        friendly_error = "خدمة الذكاء الاصطناعي مشغولة حاليًا. يرجى المحاولة مرة أخرى بعد عدة دقائق."
                    else:
                        friendly_error = "The AI image generation service is currently experiencing high traffic. Please try again in a few minutes."
                else:
                    if lang == "ar":
                        # Provide more specific Arabic error for common issues
                        if "not available in your country" in error_message.lower():
                            friendly_error = "الخدمة غير متوفرة في منطقتك. يرجى استخدام VPN."
                        elif "quota" in error_message.lower():
                            friendly_error = "تم استنفاد حصة الاستخدام. يرجى المحاولة لاحقًا."
                        else:
                            friendly_error = f"حدث خطأ أثناء معالجة الصورة: {str(e)}"
                    else:
                        friendly_error = f"Error processing image with Gemini: {str(e)}"
                
                return render_template('index.html', error=friendly_error, texts=TRANSLATIONS[lang], lang=lang, dir="rtl" if lang == "ar" else "ltr")
        
        except Exception as e:
            if lang == "ar":
                error_msg = f"خطأ في معالجة الطلب: {str(e)}"
            else:
                error_msg = f"Error processing request: {str(e)}"
            return render_template('index.html', error=error_msg, texts=TRANSLATIONS[lang], lang=lang, dir="rtl" if lang == "ar" else "ltr")
    
    return render_template('index.html', texts=TRANSLATIONS[lang], lang=lang, dir="rtl" if lang == "ar" else "ltr")

@app.route('/images/<image_id>')
def get_image(image_id):
    """API endpoint to retrieve an image by ID"""
    try:
        # Query image metadata
        response = supabase.table('images').select("*").eq("id", image_id).execute()
        
        if len(response.data) == 0:
            return jsonify({"error": "Image not found"}), 404
        
        image_data = response.data[0]
        bucket_name = "images"
        file_path = image_data['file_path']
        
        # Generate a public URL for the image
        public_url = supabase.storage.from_(bucket_name).get_public_url(file_path)
        
        return jsonify({
            "id": image_data['id'],
            "image_type": image_data['image_type'],
            "url": public_url,
            "created_at": image_data['created_at']
        })
    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/temp/<path:filename>')
def temp_files(filename):
    return send_from_directory(TEMP_FOLDER, filename)

@app.route('/gallery')
def gallery():
    # Get current language from session or default to English
    lang = session.get('lang', 'en')
    
    """Gallery page to display all saved images from Supabase"""
    try:
        supabase_client = get_supabase_client()
        if not supabase_client:
            return render_template('gallery.html', error="Failed to connect to Supabase storage", texts=TRANSLATIONS[lang], lang=lang, dir="rtl" if lang == "ar" else "ltr")
        
        # Fetch all images from storage
        original_images = []
        edited_images = []
        
        max_retries = 3
        retry_delay = 1
        
        for attempt in range(max_retries):
            try:
                # Get all objects from the images bucket
                bucket_name = "images"
                response = supabase_client.storage.from_(bucket_name).list()
                
                # Check for folders first
                folders = [item for item in response if item.get('id') is None]  # Folders usually have no ID
                
                # If we found folders, get files from each folder
                if folders:
                    for folder in folders:
                        folder_name = folder.get('name')
                        folder_files = supabase_client.storage.from_(bucket_name).list(folder_name)
                        
                        for file in folder_files:
                            file_path = f"{folder_name}/{file.get('name')}"
                            file_url = supabase_client.storage.from_(bucket_name).get_public_url(file_path)
                            
                            # Extract filename (UUID) from path
                            file_id = file.get('name').split('.')[0]
                            created_at = file.get('created_at', '')
                            
                            if folder_name == 'original':
                                original_images.append({
                                    'id': file_id,
                                    'url': file_url,
                                    'created_at': created_at
                                })
                            elif folder_name == 'edited':
                                edited_images.append({
                                    'id': file_id,
                                    'url': file_url,
                                    'created_at': created_at
                                })
                else:
                    # If no folders, use storage.objects to get all files
                    # This is a direct query to the database to get all objects
                    query = """
                    SELECT * FROM storage.objects 
                    WHERE bucket_id = 'images' 
                    ORDER BY created_at DESC;
                    """
                    
                    objects_response = supabase_client.table("storage.objects").select("*").eq("bucket_id", "images").order("created_at", desc=True).execute()
                    
                    if objects_response.data:
                        for obj in objects_response.data:
                            file_path = obj.get('name')
                            file_url = supabase_client.storage.from_(bucket_name).get_public_url(file_path)
                            file_id = file_path.split('/')[-1].split('.')[0]
                            created_at = obj.get('created_at', '')
                            
                            if file_path.startswith('original/'):
                                original_images.append({
                                    'id': file_id,
                                    'url': file_url,
                                    'created_at': created_at
                                })
                            elif file_path.startswith('edited/'):
                                edited_images.append({
                                    'id': file_id,
                                    'url': file_url,
                                    'created_at': created_at
                                })
                
                # If we reached here successfully, no need to retry
                break
                
            except requests.exceptions.ConnectionError as e:
                if attempt < max_retries - 1:
                    jitter = random.uniform(0, 0.5)
                    sleep_time = retry_delay * (2 ** attempt) + jitter
                    print(f"Connection error fetching gallery images, retrying in {sleep_time:.2f} seconds... ({attempt+1}/{max_retries})")
                    time.sleep(sleep_time)
                    # Try to get a fresh client for the next attempt
                    supabase_client = get_supabase_client()
                else:
                    print(f"Error fetching gallery images after {max_retries} attempts: {str(e)}")
                    return render_template('gallery.html', error=f"Failed to fetch images after {max_retries} attempts", texts=TRANSLATIONS[lang], lang=lang, dir="rtl" if lang == "ar" else "ltr")
            
            except Exception as e:
                print(f"Error fetching gallery images: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    supabase_client = get_supabase_client()
                else:
                    return render_template('gallery.html', error=f"Error fetching images: {str(e)}", texts=TRANSLATIONS[lang], lang=lang, dir="rtl" if lang == "ar" else "ltr")
        
        # Try to access with MCP for more reliable data
        try:
            mcp_response = supabase.query("""
                SELECT * FROM storage.objects 
                WHERE bucket_id = 'images' 
                ORDER BY created_at DESC;
            """)
            
            if mcp_response and len(original_images) == 0 and len(edited_images) == 0:
                # If the previous methods didn't work, use this data
                for obj in mcp_response:
                    file_path = obj.get('name')
                    file_url = supabase_client.storage.from_(bucket_name).get_public_url(file_path)
                    file_id = file_path.split('/')[-1].split('.')[0]
                    created_at = obj.get('created_at', '')
                    
                    if file_path.startswith('original/'):
                        original_images.append({
                            'id': file_id,
                            'url': file_url,
                            'created_at': created_at
                        })
                    elif file_path.startswith('edited/'):
                        edited_images.append({
                            'id': file_id,
                            'url': file_url,
                            'created_at': created_at
                        })
        except Exception as e:
            print(f"MCP query attempt failed: {str(e)}")
            # Continue with whatever data we've collected so far
        
        # Create pairs of original and edited images where possible
        image_pairs = []
        
        # First, try to match original images with their edited versions
        # This is a best-effort approach as we don't have direct relationships in the database
        matched_edited_ids = set()
        
        for orig in original_images:
            # Look for an edited image with the closest creation time
            closest_edited = None
            min_time_diff = float('inf')
            
            for edited in edited_images:
                if edited['id'] in matched_edited_ids:
                    continue
                
                # Compare creation times if available
                if orig.get('created_at') and edited.get('created_at'):
                    orig_time = time.strptime(orig['created_at'].split('.')[0], '%Y-%m-%dT%H:%M:%S')
                    edited_time = time.strptime(edited['created_at'].split('.')[0], '%Y-%m-%dT%H:%M:%S')
                    
                    time_diff = abs(time.mktime(edited_time) - time.mktime(orig_time))
                    
                    # If the edited image was created within 2 minutes of the original
                    # it's likely they're related
                    if time_diff < 120 and time_diff < min_time_diff:
                        min_time_diff = time_diff
                        closest_edited = edited
            
            if closest_edited:
                matched_edited_ids.add(closest_edited['id'])
                image_pairs.append({
                    'original': orig,
                    'edited': closest_edited
                })
            else:
                # No matching edited image found
                image_pairs.append({
                    'original': orig,
                    'edited': None
                })
        
        # Add any unmatched edited images
        for edited in edited_images:
            if edited['id'] not in matched_edited_ids:
                image_pairs.append({
                    'original': None,
                    'edited': edited
                })
        
        # Sort pairs by creation time of the original image (or edited if no original)
        def get_pair_time(pair):
            if pair['original'] and pair['original'].get('created_at'):
                return pair['original']['created_at']
            elif pair['edited'] and pair['edited'].get('created_at'):
                return pair['edited']['created_at']
            return ''
        
        image_pairs.sort(key=get_pair_time, reverse=True)
        
        return render_template('gallery.html', image_pairs=image_pairs, texts=TRANSLATIONS[lang], lang=lang, dir="rtl" if lang == "ar" else "ltr")
    
    except Exception as e:
        return render_template('gallery.html', error=f"Error retrieving gallery: {str(e)}", texts=TRANSLATIONS[lang], lang=lang, dir="rtl" if lang == "ar" else "ltr")

# Custom error handler for request entity too large
@app.errorhandler(RequestEntityTooLarge)
def handle_request_too_large(error):
    lang = session.get('lang', 'en')
    return render_template('index.html', 
                          error="The uploaded image is too large. Please try with a smaller image or reduce the resolution.",
                          texts=TRANSLATIONS[lang], 
                          lang=lang, 
                          dir="rtl" if lang == "ar" else "ltr"), 413

# Add dedicated healthcheck endpoint for Railway
@app.route('/healthcheck', methods=['GET'])
def healthcheck():
    """Simple health check endpoint for Railway deployment"""
    return jsonify({"status": "ok", "service": "image-editing"}), 200

if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
