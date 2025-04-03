from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify, send_from_directory, session
import os
import io
import tempfile
from google import genai
from google.genai import types
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import base64
import uuid
import time
import shutil
import re
from supabase import create_client
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
API_KEY = "AIzaSyBbE0FW-7SEm1FW0NgusR18GmsV10aAVYE"

# Supabase Configuration
SUPABASE_URL = "https://ydmzuujthdrokuosbvyt.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlkbXp1dWp0aGRyb2t1b3Nidnl0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDMzNDA0OTMsImV4cCI6MjA1ODkxNjQ5M30.YYtcgWWV59AcM30JUbq91yYVgGGkU8pk3kNofiZC19I"

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
            
            # Upload the file to Supabase Storage with retry mechanism
            response = supabase_client.storage.from_(bucket_name).upload(
                file_path, 
                img_bytes, 
                {"content-type": "image/png"}
            )
            
            # Get public URL
            public_url = supabase_client.storage.from_(bucket_name).get_public_url(file_path)
            
            # Skip database insertion for now as the table might not exist
            # Instead, just return the successful upload information
            print(f"Successfully uploaded image to {file_path}")
            
            return image_id, public_url
        
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
                return None, None
        
        except Exception as e:
            print(f"Error storing image in Supabase: {str(e)}")
            # For non-connection errors, we'll still retry but with less backoff
            if attempt < max_retries - 1:
                time.sleep(retry_delay)
                # Try to get a fresh client for the next attempt
                supabase_client = get_supabase_client()
            else:
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
                    processed_prompt = prompt
                
                for attempt in range(max_retries):
                    try:
                        # Generate content using Gemini with clear safety settings for image editing
                        response = client.models.generate_content(
                            model="gemini-2.0-flash-exp-image-generation",
                            contents=[processed_prompt, image],
                            config=types.GenerateContentConfig(
                                response_modalities=["Text", "Image"],
                                temperature=0.2,  # Lower temperature for more deterministic results
                                top_k=20,
                                top_p=0.8
                            )
                        )
                        
                        # If we got here, the request succeeded
                        break
                    except Exception as e:
                        last_error = e
                        error_message = str(e)
                        
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
                
                # Process the response
                response_text = ""
                result_image = None
                result_image_b64 = None
                
                try:
                    # Process the text response with special handling for Arabic
                    for part in response.candidates[0].content.parts:
                        if part.text is not None:
                            # Add text direction marker for Arabic responses if needed
                            if lang == "ar" and not part.text.strip().startswith('﷽') and not part.text.strip().startswith('بسم الله'):
                                # Ensure proper Arabic text direction and formatting
                                response_text += part.text
                            else:
                                response_text += part.text
                        elif part.inline_data is not None:
                            result_image = Image.open(BytesIO(part.inline_data.data))
                            
                            # Compress the result image if needed before converting to base64
                            if result_image.width * result_image.height > 1500000:
                                result_image = compress_image(result_image)
                                
                            result_image_b64 = image_to_base64(result_image)
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
                                            result_image = Image.open(BytesIO(part.inline_data.data))
                                            result_image_b64 = image_to_base64(result_image)
                    except Exception as inner_e:
                        print(f"Alternative response parsing also failed: {str(inner_e)}")
                
                if not result_image_b64:
                    # Special message for Arabic users
                    if lang == "ar":
                        error_msg = "فشل في إنشاء الصورة المعدلة. يرجى المحاولة مرة أخرى بتعليمات مختلفة."
                    else:
                        error_msg = "Failed to generate edited image."
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

if __name__ == '__main__':
    app.run(debug=True)
