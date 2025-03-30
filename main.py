from flask import Flask, render_template, request, redirect, url_for, send_file
import os
from google import genai
from google.genai import types
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import base64

# Configuration
API_KEY = "AIzaSyBbE0FW-7SEm1FW0NgusR18GmsV10aAVYE"
UPLOAD_FOLDER = 'static/uploads'
RESULT_FOLDER = 'static/results'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Initialize Flask app
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['RESULT_FOLDER'] = RESULT_FOLDER

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
        
        # Check if file is provided
        if 'file' not in request.files:
            return render_template('index.html', error="Please upload an image.")
        
        file = request.files['file']
        
        # Check if file is valid
        if file.filename == '':
            return render_template('index.html', error="No file selected.")
        
        if not allowed_file(file.filename):
            return render_template('index.html', error="File type not allowed. Please upload PNG or JPG images.")
        
        # Save the uploaded file
        image_path = os.path.join(app.config['UPLOAD_FOLDER'], 'input_image.png')
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
            
            for part in response.candidates[0].content.parts:
                if part.text is not None:
                    response_text += part.text
                elif part.inline_data is not None:
                    result_image = Image.open(BytesIO(part.inline_data.data))
                    result_path = os.path.join(app.config['RESULT_FOLDER'], 'result_image.png')
                    result_image.save(result_path)
            
            return render_template('index.html', 
                                  prompt=prompt, 
                                  original_image='uploads/input_image.png', 
                                  result_image='results/result_image.png',
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
