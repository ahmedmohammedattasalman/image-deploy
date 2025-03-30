from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify
import os
from google import genai
from google.genai import types
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import base64
import uuid
import time

# Configuration
API_KEY = "AIzaSyBbE0FW-7SEm1FW0NgusR18GmsV10aAVYE"
UPLOAD_FOLDER = 'static/uploads'
RESULT_FOLDER = 'static/results'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Initialize Flask app
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULT_FOLDER'] = RESULT_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload size

# Create directories if they don't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(RESULT_FOLDER, exist_ok=True)

# Initialize Gemini client
client = genai.Client(api_key=API_KEY)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Create a sample image if ahmed.png doesn't exist
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
    
    # Save the image
    sample_path = os.path.join(app.config['UPLOAD_FOLDER'], 'sample_image.png')
    image.save(sample_path)
    return sample_path

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
            last_result_path = os.path.join(app.config['RESULT_FOLDER'], 'result_image.png')
            
            if not os.path.exists(last_result_path):
                return render_template('index.html', error="Previous result not found. Please start with a new image.")
            
            # Use the existing result as input
            image_path = last_result_path
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
            
            # Save the uploaded file with a unique name to avoid caching issues
            timestamp = int(time.time())
            input_filename = f'input_image_{timestamp}.png'
            image_path = os.path.join(app.config['UPLOAD_FOLDER'], input_filename)
            file.save(image_path)
        
        # Process the image with Gemini
        try:
            image = Image.open(image_path)
            
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
            result_path = None
            timestamp = int(time.time())
            result_filename = f'result_image_{timestamp}.png'
            
            for part in response.candidates[0].content.parts:
                if part.text is not None:
                    response_text += part.text
                elif part.inline_data is not None:
                    result_image = Image.open(BytesIO(part.inline_data.data))
                    # Save with timestamp to avoid browser caching old images
                    result_path = os.path.join(app.config['RESULT_FOLDER'], result_filename)
                    # Also save as the standard result_image.png for continued edits
                    standard_result_path = os.path.join(app.config['RESULT_FOLDER'], 'result_image.png')
                    
                    result_image.save(result_path)
                    result_image.save(standard_result_path)
            
            # Determine which original image to display
            if continue_edit:
                # For continued edits, use the previous result_image.png as original
                original_image_path = 'uploads/input_image.png' if os.path.exists(os.path.join(UPLOAD_FOLDER, 'input_image.png')) else image_path.replace(app.config['UPLOAD_FOLDER'], 'uploads')
            else:
                # Save a copy of the input as the standard input_image.png
                input_copy_path = os.path.join(app.config['UPLOAD_FOLDER'], 'input_image.png')
                image.save(input_copy_path)
                original_image_path = 'uploads/' + os.path.basename(image_path)
            
            return render_template('index.html', 
                                  prompt=prompt, 
                                  original_image=original_image_path, 
                                  result_image=f'results/{result_filename}',
                                  response_text=response_text)
        
        except Exception as e:
            return render_template('index.html', error=f"Error processing image: {str(e)}")
    
    return render_template('index.html')

@app.route('/static/<path:filename>')
def static_files(filename):
    return send_file(os.path.join('static', filename))

if __name__ == '__main__':
    # Create a sample image if ahmed.png doesn't exist anymore
    if not os.path.exists('ahmed.png') and not os.path.exists(os.path.join(UPLOAD_FOLDER, 'input_image.png')):
        create_sample_image()
        print("Created a sample image at static/uploads/sample_image.png for testing purposes.")
    
    app.run(debug=True)
