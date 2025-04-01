from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify, send_from_directory
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

# Load environment variables
load_dotenv()

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
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size
app.config['SESSION_TYPE'] = 'filesystem'  # For session storage

# Initialize Gemini client
client = genai.Client(api_key=API_KEY)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Helper to convert base64 to image
def base64_to_image(base64_str):
    # Remove data URI prefix if present
    if 'base64,' in base64_str:
        base64_str = base64_str.split('base64,')[1]
    
    # Decode base64 to binary
    img_data = base64.b64decode(base64_str)
    return Image.open(BytesIO(img_data))

# Helper to convert image to base64
def image_to_base64(img):
    buffered = BytesIO()
    img.save(buffered, format="PNG")
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

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        try:
            # Check if prompt is provided
            if 'prompt' not in request.form:
                return render_template('index.html', error="Please provide a prompt.")
            
            prompt = request.form['prompt']
            
            # Check if this is a continued edit
            continue_edit = request.form.get('continue_edit') == 'true'
            
            if continue_edit:
                # Get the previous result from hidden form field
                prev_result_b64 = request.form.get('previous_result_b64', '')
                
                if not prev_result_b64:
                    return render_template('index.html', error="Previous result not found. Please start with a new image.")
                
                try:
                    # Convert base64 to image for processing
                    image = base64_to_image(prev_result_b64)
                    
                    # Save original image base64 for comparison
                    original_image_b64 = request.form.get('original_image_b64', prev_result_b64)
                except Exception as e:
                    return render_template('index.html', error=f"Error processing previous edit: {str(e)}")
            else:
                # Normal flow - check for file upload
                if 'file' not in request.files:
                    return render_template('index.html', error="Please upload an image.")
                
                file = request.files['file']
                
                # Check if file is valid
                if file.filename == '':
                    return render_template('index.html', error="No file selected.")
                
                if not allowed_file(file.filename):
                    return render_template('index.html', error="File type not allowed. Please upload PNG or JPG images.")
                
                # Read the image directly
                image = Image.open(file.stream)
                
                # Store the original image in Supabase
                original_id, original_url = None, None
                try:
                    original_id, original_url = store_image_supabase(image, "original")
                    if not original_url:
                        print("Warning: Failed to store original image in Supabase, continuing with local processing")
                except Exception as e:
                    print(f"Error storing original image: {str(e)}")
                    # Continue with local processing if Supabase storage fails
                
                # Convert to base64 for original image reference
                original_image_b64 = image_to_base64(image)
            
            # Process the image with Gemini
            try:
                # Generate content using Gemini
                response = client.models.generate_content(
                    model="gemini-2.0-flash-exp-image-generation",
                    contents=[prompt, image],
                    config=types.GenerateContentConfig(
                        response_modalities=["Text", "Image"]
                    )
                )
                
                # Process the response
                response_text = ""
                result_image = None
                result_image_b64 = None
                
                for part in response.candidates[0].content.parts:
                    if part.text is not None:
                        response_text += part.text
                    elif part.inline_data is not None:
                        result_image = Image.open(BytesIO(part.inline_data.data))
                        result_image_b64 = image_to_base64(result_image)
                
                if not result_image_b64:
                    return render_template('index.html', error="Failed to generate edited image.")
                
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
                first_original_b64 = original_image_b64 if not continue_edit else request.form.get('first_original_b64', original_image_b64)
                
                # Create response with the base64 images
                return render_template('index.html', 
                                    prompt=prompt, 
                                    original_image_b64=original_image_b64,
                                    result_image_b64=result_image_b64,
                                    first_original_b64=first_original_b64,
                                    response_text=response_text,
                                    is_b64_image=True,
                                    supabase_original_url=original_url if 'original_url' in locals() and original_url else None,
                                    supabase_edited_url=edited_url if 'edited_url' in locals() and edited_url else None)
            
            except Exception as e:
                return render_template('index.html', error=f"Error processing image with Gemini: {str(e)}")
        
        except Exception as e:
            return render_template('index.html', error=f"Error processing request: {str(e)}")
    
    return render_template('index.html')

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
    """Gallery page to display all saved images from Supabase"""
    try:
        supabase_client = get_supabase_client()
        if not supabase_client:
            return render_template('gallery.html', error="Failed to connect to Supabase storage")
        
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
                    return render_template('gallery.html', error=f"Failed to fetch images after {max_retries} attempts")
            
            except Exception as e:
                print(f"Error fetching gallery images: {str(e)}")
                if attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    supabase_client = get_supabase_client()
                else:
                    return render_template('gallery.html', error=f"Error fetching images: {str(e)}")
        
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
        
        return render_template('gallery.html', image_pairs=image_pairs)
    
    except Exception as e:
        return render_template('gallery.html', error=f"Error retrieving gallery: {str(e)}")

if __name__ == '__main__':
    app.run(debug=True)
