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

# Configuration
API_KEY = "AIzaSyBbE0FW-7SEm1FW0NgusR18GmsV10aAVYE"
TEMP_FOLDER = tempfile.mkdtemp()  # Create temporary directory for session
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Initialize Flask app
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

# Initialize Gemini client
client = genai.Client(api_key=API_KEY)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Cleanup temporary files on shutdown
@app.teardown_appcontext
def cleanup_temp_files(exception=None):
    try:
        shutil.rmtree(TEMP_FOLDER)
    except:
        pass

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
        # Check if prompt is provided
        if 'prompt' not in request.form:
            return render_template('index.html', error="Please provide a prompt.")
        
        prompt = request.form['prompt']
        
        # Check if this is a continued edit
        continue_edit = request.form.get('continue_edit') == 'true'
        
        if continue_edit:
            # Use the last result image as the input for the next edit
            if 'last_result' not in request.cookies:
                return render_template('index.html', error="Previous result not found. Please start with a new image.")
            
            # Get last result from cookie
            last_result_path = request.cookies.get('last_result')
            if not os.path.exists(last_result_path):
                return render_template('index.html', error="Previous result not found. Please start with a new image.")
            
            # Use the existing result as input
            image = Image.open(last_result_path)
            original_image_path = request.cookies.get('original_image', last_result_path)
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
            
            # Read the image directly without saving
            image = Image.open(file.stream)
            
            # Save a temporary copy for display
            timestamp = int(time.time())
            original_filename = f'input_image_{timestamp}.png'
            original_image_path = os.path.join(TEMP_FOLDER, original_filename)
            image.save(original_image_path, format="PNG", quality=100)
        
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
            timestamp = int(time.time())
            result_filename = f'result_image_{timestamp}.png'
            result_image_path = os.path.join(TEMP_FOLDER, result_filename)
            
            for part in response.candidates[0].content.parts:
                if part.text is not None:
                    response_text += part.text
                elif part.inline_data is not None:
                    result_image = Image.open(BytesIO(part.inline_data.data))
                    # Save in temporary location
                    result_image.save(result_image_path, format="PNG", quality=100)
            
            # Set paths for template
            if not continue_edit:
                template_original_path = original_image_path
            else:
                template_original_path = original_image_path
            
            # Create response
            response = render_template('index.html', 
                                 prompt=prompt, 
                                 original_image=template_original_path,
                                 result_image=result_image_path,
                                 response_text=response_text,
                                 is_temp_file=True)
            
            # Set cookies for future edits
            resp = app.make_response(response)
            resp.set_cookie('last_result', result_image_path)
            if not continue_edit:
                resp.set_cookie('original_image', original_image_path)
            
            return resp
        
        except Exception as e:
            return render_template('index.html', error=f"Error processing image: {str(e)}")
    
    return render_template('index.html')

@app.route('/temp/<path:filename>')
def temp_files(filename):
    return send_from_directory(TEMP_FOLDER, filename)

if __name__ == '__main__':
    app.run(debug=True)
