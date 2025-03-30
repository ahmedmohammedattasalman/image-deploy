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

# Configuration
API_KEY = "AIzaSyBbE0FW-7SEm1FW0NgusR18GmsV10aAVYE"
# Create temporary directory for session
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
                result_image_b64 = None
                
                for part in response.candidates[0].content.parts:
                    if part.text is not None:
                        response_text += part.text
                    elif part.inline_data is not None:
                        result_image = Image.open(BytesIO(part.inline_data.data))
                        result_image_b64 = image_to_base64(result_image)
                
                if not result_image_b64:
                    return render_template('index.html', error="Failed to generate edited image.")
                
                # If it's not a continued edit, the current image is the first original
                first_original_b64 = original_image_b64 if not continue_edit else request.form.get('first_original_b64', original_image_b64)
                
                # Create response with the base64 images
                return render_template('index.html', 
                                    prompt=prompt, 
                                    original_image_b64=original_image_b64,
                                    result_image_b64=result_image_b64,
                                    first_original_b64=first_original_b64,
                                    response_text=response_text,
                                    is_b64_image=True)
            
            except Exception as e:
                return render_template('index.html', error=f"Error processing image with Gemini: {str(e)}")
        
        except Exception as e:
            return render_template('index.html', error=f"Error processing request: {str(e)}")
    
    return render_template('index.html')

@app.route('/temp/<path:filename>')
def temp_files(filename):
    return send_from_directory(TEMP_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)
